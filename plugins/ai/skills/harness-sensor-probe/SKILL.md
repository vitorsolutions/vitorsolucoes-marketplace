---
name: harness-sensor-probe
description: >-
  Proves that a project's automated checks really fail, by adding one deliberately defective file,
  running the same command the coding agent runs to decide it is done, recording which checks
  catch the defects and whether they fail the command or only warn, and then removing the file
  with a cleanup that also runs on failure. Turns "I configured the checks" into "I watched them
  fire". Classifies each control as enforced, reported, silent, or inconclusive. Currently
  supports .NET and Python. Use when the user asks to "verify the checks actually fail", "test
  the sensors", "prove the build blocks bad code", "check that the harness works", "validar se as
  verificações realmente falham", "testar se o build barra código inseguro", or right after
  configuring checks with harness-sensors. Do NOT use it to configure the checks (harness-sensors),
  to fix what it finds, or to scan existing code for vulnerabilities.
---

# Harness sensor probe

## What this skill does

A check can be configured and still never stop anything: the rule is off, the file is excluded, the failure setting is missing, or the command is wrapped so that it always succeeds. This skill finds out by trying. It adds one file with known defects, runs the project's real verification command, and reads what happened.

Vocabulary:

- **Probe**: the temporary file containing deliberately defective code.
- **Verification command**: the command the agent (or CI) runs to decide that a task is done.
- **Result classes**:
  - **enforced**: the defect is reported and the command exits with failure.
  - **reported**: the defect is reported but the command exits with success. It is only a warning.
  - **silent**: the defect is not reported at all (rule off, or code not analyzed).
  - **inconclusive**: the result cannot be trusted (for example the command failed for an unrelated reason before analysis, or the baseline already exits with failure so the exit status says nothing about the probe).

## Hard rules

- Create exactly one new file. Never edit or delete anything that existed before the probe.
- Refuse to run if the probe path already exists. Use the alternative name from the pack, or ask. Never reuse, overwrite, or delete the existing file.
- The probe is removed even if the command fails or is interrupted. Run the check and the removal inside one command that guarantees cleanup (for example a shell `trap`, or `try`/`finally`). A `trap` does not run when the process is killed with SIGKILL or the machine loses power, so the confirmation after the run (and a check at the start of the next one) is the fallback: if the probe is still there, remove that one file, say so, and report it.
- Write the captured output of the check outside the repository (a temporary folder), never next to the code. The probe must be the only file the run adds.
- After the run, confirm the probe is gone and that no other file changed. Report any difference.
- The probe is deliberately insecure. Never copy any part of it into real code, and put a comment at the top saying it is temporary.
- Never fix the defects the probe reveals in the real code. Never change configuration. Report only.
- Never commit, push, or stage files.
- Never install packages or use the network without asking.
- Match diagnostics by code and by the probe's file path, never by message text.

## Workflow

### 1. Detect the stack

Find the markers in each stack reference under `references/stacks/` and read only the matching pack. Several stacks: handle each separately. No matching pack: say the stack is not supported, and change nothing.

### 2. Find the verification command

Ask which command the agent or CI runs to decide a task is done. If the repository has an agent guide with a definition of done, propose those commands. Use the project's own command, not a shortcut, because the point is to test what the agent really runs.

If the full command is slow, you may run a faster scoped version, but say so in the report. A scoped run proves the tool's configuration, not the command as the agent runs it.

### 3. Baseline

Run the verification command once without the probe. Record the exit status and the diagnostics by code. A full build or lint can take minutes: tell the user the expected time, set a timeout above it, and use the scoped version of step 2 if it is too slow.

If the baseline already exits with failure, the exit status of the probe run cannot prove that the probe was caught, even when the probe's diagnostics appear as errors. Classify every control as **inconclusive** by exit status, and list the probe's diagnostics (matched by code and the probe's file path) as a separate observation. Say that the baseline must be made to pass first. A failure that stops analysis early is inconclusive for the same reason.

### 4. Choose the placement and confirm

Use the pack's placement rules. Tell the user the exact path and the defects the probe contains, and ask for confirmation. The placement matters: the file must be inside code the tools analyze.

### 5. Run the probe

1. Record the repository state (the list of changed and untracked files).
2. Create the probe from the snippets in the pack.
3. Run the verification command, with cleanup guaranteed in the pack's form. On Windows, say which shell was used, because the PowerShell form and the POSIX `trap` form differ.
4. Capture the exit status and the diagnostics whose file path is the probe.
5. Confirm the probe is removed and the repository state matches step 1.

### 6. Classify and report

For each control the probe targets:

| Control | Expected codes | Observed | Class | Notes |
| --- | --- | --- | --- | --- |

Expected codes depend on tool versions. Match by the control's category. If a different code of the same category appears, report it as observed. Do not mark the control missing because the exact code differs.

Then say:

- Which controls are enforced, reported, silent, and inconclusive.
- What the user would change for each reported or silent one (name the skill that does it, such as `harness-sensors`). Do not change it yourself.
- Whether the run was scoped or full.
- Anything that looks like a bypass of the command, if the exit status does not match what the diagnostics imply.
- The known limits below.

## Known limits to state

- The probe checks only the defect classes it contains. A control that is not covered by a probe snippet is not tested.
- Passing the probe does not mean the project is secure. It means these specific checks fire.
- A control that is enforced for the probe's location may be disabled elsewhere, for example by a per-directory configuration. Test where it matters.
- Tool updates change rule sets. Run the probe again after upgrading tools.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. Placement rules (where the probe goes, how to avoid exclusions and generated-code exemptions)
3. Probe snippets, each tagged with the control it targets and the diagnostic codes it should produce
4. How to run the check with guaranteed cleanup, and how to read the output
5. How to classify results for this stack
6. Pitfalls and limits
7. Verified on (date, and what was not re-verified)
