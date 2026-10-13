---
name: harness-setup
description: >-
  Assesses how well a repository is prepared for AI coding agents and produces an ordered
  adoption plan, without changing anything. Detects the stack, checks each layer of the harness
  (reproducible builds, failing checks, style, banned APIs, architecture rules, tests, the agent
  guide, permissions, hooks, CI, proof that the checks fire), classifies each as present,
  partial, missing, or unknown with evidence, and recommends which harness skill to run next and
  in what order, in strict or gradual mode. It only plans and delegates: each step is carried out
  by its own skill, and every skill can also be used on its own. Currently supports .NET and
  Python. Use when the user asks to "set up the harness", "prepare this repo for coding agents",
  "what is missing for agents to work well here", "assess my project for AI agents", "plan the
  agent setup", "preparar este repositório para agentes", "avaliar o harness do projeto",
  "o que falta configurar para o agente", or does not know which harness skill to start with. Do
  NOT use it to apply changes itself, to review code quality, or to audit dependencies for
  vulnerabilities.
---

# Harness setup

## What this skill does

A coding agent is only as reliable as what surrounds it: checks that fail, rules it can read, limits it cannot cross, and evidence that these work. This skill looks at a repository, tells the user which of those layers exist, and proposes the order in which to build the missing ones. It does not build anything.

Vocabulary:

- **Harness**: everything around the model that guides it before it acts or checks it after, such as instruction files, automated checks, permissions, and hooks.
- **Layer**: one concern of the harness, covered by one skill.
- **Plan**: the ordered list of skills to run, with the reason for each.

## Hard rules

- Read-only. Never create, edit, or delete a file, and never commit or stage anything.
- Never run a build, test, restore, or any command that writes files, uses the network, or takes long, without asking. Version commands, effective-state readouts, and file reads are allowed.
- Never invent evidence. Every state in the plan cites what was read or run. If a layer could not be evaluated, say **unknown** and why.
- Never carry out a module's work yourself. When the user picks a step, hand off to that skill.
- Never claim the harness is "complete" or "secure". Report layers and evidence.
- Do not copy configuration or secrets into the report. Cite file names and setting names only.

## The layers and their skills

| Order | Layer | Skill | Question it answers |
| --- | --- | --- | --- |
| 1 | Reproducible environment | `harness-reproducibility` | Do all machines and CI resolve the same toolchain and dependency versions? |
| 2 | Checks that fail | `harness-sensors` | Do correctness, type, and security checks fail the verification command? |
| 3 | Style | `harness-code-style` | Is style verified by a tool and does it fail on violation? |
| 4 | Banned APIs | `harness-banned-apis` | Are "do not use X" policies enforced by a check? |
| 5 | Tests | `harness-test-baseline` | Is there a usable test project and command? |
| 6 | Architecture rules | `harness-architecture-guard` | Are dependency rules between modules checked automatically? |
| 7 | Agent guide | `harness-agent-guide` | Does the agent have accurate instructions and a definition of done? |
| 8 | Permissions | `harness-permissions` | Are the agent's allowed and denied actions set for this project? |
| 9 | Hooks | `harness-hooks` | Are the rules enforced at run time (done criteria, protected files, suppressions, risky commands)? |
| 10 | CI | `harness-ci-pipeline` | Does CI repeat the local definition of done and keep evidence? |
| 11 | Proof | `harness-sensor-probe` | Has anyone watched the checks fail on defective code? |

Layer 6 only applies to projects with more than one module and a dependency direction to protect. Mark it **not applicable** otherwise, with the reason.

## Workflow

### 1. Detect the stack

Find the markers in each stack reference under `references/stacks/`. Several stacks (for example .NET and Python in one repository): read every matching pack, assess the stack-specific layers (1 to 6) separately, and assess the repository-wide layers (7 to 10: guide, permissions, hooks, CI) once, then reference them from each plan instead of repeating or contradicting them. No matching pack: say the stack is not supported yet, explain the layers in concept, and stop.

If a pack's "Verified on" date is more than a few months old, say so.

### 2. Assess each layer

Use the stack reference, which lists for each layer the files and settings that show it exists. Classify each layer:

- **present**: the signals exist and, where checkable, enforce what the layer is for.
- **partial**: some signals exist but the layer does not fully do its job (for example, checks configured but only warning, or a guide that lists commands that no longer work).
- **missing**: no signal found.
- **unknown**: not evaluated, with the reason (for example a command would have to be run and the user declined).
- **not applicable**: with the reason.

Rules for judging:

- A configured check that only prints warnings is **partial**, not present.
- Agent-specific layers (permissions, hooks) live in files that depend on the agent. Look in the locations the pack names for the agent the user works with. If you do not know where another agent keeps them, say **unknown** instead of guessing.
- Checking that the commands in an agent guide or CI file "fail" means running them. Without permission, check only that they exist by reading, and say the rest is unverified.
- A tool the pack needs but that is not installed makes everything depending on it **unknown**. Never install it to find out.
- Presence is not proof. The proof layer is **present** only if someone has run the probe and recorded the result. Otherwise it is **missing** even when the checks look right.

### 3. Decide the mode

If the user's repository already has many violations in the baseline, recommend gradual mode for the checks layers, and say why. If warnings do not fail the build and the baseline has not been measured, say so, recommend gradual mode as the provisional default, and name `harness-sensors` as the step that measures it. Do not run a build to measure it unasked.

### 4. Build the plan

Order the steps by dependency:

- Steps 1 to 5 prepare the ground, in table order.
- The guide (7) comes after checks and tests, because its definition of done lists commands that must pass.
- Hooks (9) come after the guide, because they enforce what it states.
- CI (10) comes after the definition of done is settled.
- Proof (11) comes last and can be repeated after each change.

Skip layers that are already **present**, and say so. Do not recommend a step just because it exists.

### 5. Present the plan

Use this shape:

**Repository**: stack, toolchain version found, and what was run.

**Layer state**

| Layer | State | Evidence | Skill |
| --- | --- | --- | --- |

**Plan**

| Step | Skill | Why | Mode | Writes to the repository? | Risk | Depends on |
| --- | --- | --- | --- | --- | --- | --- |

Mode is **strict** or **gradual** where it applies, otherwise a dash. Risk is **low** (reads or small additive files), **medium** (edits existing configuration), or **high** (writes agent configuration such as hooks or permissions).

**Not evaluated**: the layers that are unknown, and what would be needed to evaluate them.

**Limits**: the notes below.

**Next action**: ask which step the user wants to start with. Recommend one, with the reason, but let the user choose. If every layer is **present** or **not applicable**, say there is nothing to build, and offer to repeat the proof (`harness-sensor-probe`) only if the pack's staleness check shows it predates the last tool or configuration change.

### 6. Hand off

When the user picks a step, invoke that skill by name (a request such as "fix the checks" means layer 2, `harness-sensors`; if the user means style or banned APIs, hand off to layers 3 or 4 instead; ask when it is unclear) and let it run its own workflow. Do not repeat its questions. If the skill is not available in the environment, say so, describe what the step would do, and stop.

After a step finishes, the user can ask for the assessment again. The plan is not stored. Reassessing recomputes it from the repository.

## Known limits to state

- This assessment reads files and settings. It does not measure how well the harness works.
- The proof layer is the only evidence that checks fire, and it covers only the defect classes it tests.
- Signals differ by tool and version. An unrecognized setup is reported as unknown, not as missing.
- A complete set of layers does not make code correct or secure. Business rules, dynamic testing, and review are outside this harness.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. Toolchain version command and any read-only effective-state readout
3. For each layer, the signals that show it exists in this stack, and what makes it only partial
4. Where to look for agent-specific files
5. Pitfalls and limits
6. Verified on (date, and what was not re-verified)
