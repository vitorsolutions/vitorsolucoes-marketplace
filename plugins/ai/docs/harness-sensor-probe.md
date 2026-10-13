# Harness Sensor Probe

Proves that a project's automated checks really fail, by adding one deliberately defective file, running the command your coding agent runs, and reporting what happened before removing the file.

## Why this skill exists

A check can be configured and still stop nothing: the rule is off, the file is excluded, the failure setting is missing, or the command is wrapped so that it always succeeds. Reading configuration does not reveal that. Trying does.

## What it does

- Detects the stack and asks which command the agent or CI runs to decide a task is done.
- Records a baseline run without the probe.
- Adds one new file with known defects (insecure query construction, a weak hash, a null dereference, or their equivalents), after you confirm where it goes.
- Runs the real verification command with a cleanup that also runs on failure.
- Classifies each control as enforced, reported, silent, or inconclusive, and confirms the probe is gone and nothing else changed.

## Result classes

| Class | Meaning |
| --- | --- |
| enforced | The defect is reported and the command fails. |
| reported | The defect is reported but the command still succeeds, so it is only a warning. |
| silent | The defect is not reported at all. |
| inconclusive | The result cannot be trusted, for example the command failed early for an unrelated reason. |

## Supported stacks

| Stack | Defect classes probed |
| --- | --- |
| .NET | Insecure query construction, broken hash algorithm, null dereference |
| Python | Insecure query construction, weak hash, mutable default argument, missing type annotations |

Each stack lives in a reference file under `references/stacks/`.

## What it will not do

- Edit or delete any existing file, fix what it finds, or change configuration.
- Overwrite a file that already exists at the probe path. It uses an alternative probe name instead.
- Classify controls when the baseline already fails: they are reported as inconclusive until the baseline is green.
- Write the tools' output into the repository: it goes to a temporary folder.
- Leave the probe behind: removal runs even when the command fails.
- Commit or stage anything.

## When to use it

Right after configuring checks with `harness-sensors`, after upgrading tools, or whenever you want evidence that the checks block bad code: "verify the checks actually fail", "prove the build blocks insecure code".

## Limits

The probe covers only the defect classes it contains. Passing it does not mean the project is secure, only that these checks fire where the probe was placed. A control can be enforced in one location and disabled in another, so place the probe where it matters.
