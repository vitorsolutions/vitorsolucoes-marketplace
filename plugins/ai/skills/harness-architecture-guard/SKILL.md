---
name: harness-architecture-guard
description: >-
  Turns the dependency rules between a project's layers or modules into automated checks that
  fail, so a coding agent cannot quietly reach across an architectural boundary. Reads the real
  dependency structure of the code instead of trusting folder names, confirms the intended rules
  with the user, creates the guard (a new test project or a configuration file, never edits
  production code), adds controls that stop a rule from passing because it looked at nothing, and
  proves each rule fires by planting a violation in a throwaway copy. Handles code that already
  breaks a rule with a list of known violations that can only shrink. Currently supports .NET and
  Python. Use when the user asks to "enforce the dependency rule", "stop the domain from
  depending on infrastructure", "add architecture tests", "make the agent respect the layers",
  "criar testes de arquitetura", "impedir que o domínio dependa da infraestrutura", "garantir a
  regra de dependência entre camadas", or wants layering rules checked by the build. Do NOT use it
  to review an architecture, to move or refactor code, or for projects with no layers or modules
  to protect.
---

# Harness architecture guard

## What this skill does

A coding agent takes the shortest path to a working result, and the shortest path often crosses a boundary: the core logic starts to use a framework type, an inner layer imports an outer one. Review does not scale with an agent's speed. This skill makes the boundary a check that fails.

Vocabulary:

- **Layer or module**: a unit of the code with a stated place in the dependency direction.
- **Dependency rule**: "unit A must not depend on unit B or on library C".
- **Guard**: the automated check that holds the rules.
- **Vacuous pass**: a rule that passes because it matched no code, for example a misspelled name. It looks green and protects nothing.
- **Known violations**: existing breaches the team accepts for now, kept in an explicit list that can only get shorter.

## Hard rules

- Never edit production code to satisfy a rule, move code, or add or remove project references or imports. This skill adds a guard and reports violations.
- Never infer layers from folder or project names. Build the structure from the real dependency graph and ask the user to confirm the intended layering.
- Never write a rule without a control that shows it can see code. A rule that cannot fail is worse than no rule.
- Prove every rule fires by planting a violation in a throwaway copy, never in the real repository.
- Never install packages, use the network, or add a development dependency without asking.
- Never commit, push, or stage files.
- Keep the rule set small. Each rule must have a reason the user can state.

## Workflow

### 1. Detect the stack and decide whether this applies

Find the markers in each stack reference under `references/stacks/` and read each matching pack. A repository with two stacks gets one guard per stack, each in its own tool and location. No matching pack: explain the idea in concept and change nothing.

Then check that there is something to protect: more than one module with a dependency direction, or an inner module that must stay free of a library. With a single module, ask once whether it must stay free of a named library; if the answer is no, report **not applicable** with the reason and stop.

### 2. Read the real structure

Use the pack's commands to list the modules and the dependencies between them, and the libraries each one uses. Present a direction map with evidence (which module depends on which). Mention any dependency that points the wrong way according to the layering you would expect, and say it is a finding, not something you fix.

### 3. Confirm the rules with the user

Propose a small set from these kinds, and ask the user to confirm, change or drop each one:

- **Direction**: an inner module must not depend on an outer one.
- **Library leak**: an inner module must not depend on a named framework or library.
- **Independence**: two modules must not depend on each other (only if the user states it).

For each rule, write one sentence of reason. Do not add rules the user did not approve.

### 4. Measure existing violations

Run the rules in check mode against the current code, read-only, and list what breaks, by module and name. If nothing breaks, the guard can start strict. If something breaks, offer:

- **Known-violations list**: the current breaches are recorded by name. New ones fail. A listed breach that no longer fails also fails, so the list can only shrink.
- **Fix first**: the user fixes them before the guard is turned on. You do not do it.

### 5. Create the guard

Follow the pack. Create new files only, and show them before writing. The one allowed change to an existing file is registering a new guard project in the solution or configuration list, and only with approval, because a guard that is not registered is skipped without any warning. Include, in every guard:

1. The rules.
2. A control that each layer or module is actually scanned and is not empty.
3. A control that every forbidden target name really exists, so a misspelled name cannot pass. For a name that belongs to the project, the pack's guard test does it. For a name outside the project (a library), use the pack's existence check, and if the pack has none, mark the rule as needing the planted proof in step 7.
4. A positive control: one real, allowed dependency that the scan must see, which shows the scan is working.

### 6. Run it

With permission (it may restore packages), run the guard command and record its exit status and counts. A guard that reports zero checks is not working. Check that the result lists the guard's own checks by name or that the count equals the number you wrote, because a guard that is not registered is skipped while the rest of the suite still passes.

### 7. Prove each rule fires

Copy the repository to a temporary folder, leaving out build outputs, dependency folders, and version-control history. In the copy, plant one violation for each rule, run the guard there, and check that exactly that rule fails and names the offender. Delete the copy. Leave the real repository untouched, and confirm that afterward.

Some rules cannot be proven by adding the obvious dependency, because the build rejects it (a circular project reference is one). Use the pack's alternative. If there is none, or if copying is not practical, say so, and report the rule as **written but not proven**. Never write "proven" for it.

### 8. Wire it in

Do not edit the agent guide or the pipeline yourself. Say which command to add to the definition of done, and mention `harness-agent-guide` and `harness-ci-pipeline`.

### 9. Report

| Rule | Reason | Existing violations | Control | Proven by |
| --- | --- | --- | --- | --- |

Then list: files created, the command to run, known violations (with the instruction that the list must shrink), what the guard cannot see, and the limits below.

## Answering questions about an existing guard

When the user asks to review a rule, to understand a failure, or what the guard cannot do, do not install or change anything. Read the guard, check each rule against the controls in step 5 and the pitfalls in the pack, and answer from the known limits below. A rule that looks right but names nothing the scan can see is the usual finding.

## Known limits to state

- **The guard sees the dependencies the tool can see.** The tools here analyze compiled types or import statements. They do not see dynamic loading, reflection, configuration-driven wiring, or behavior that belongs in the wrong layer without a forbidden dependency.
- **Business logic in the wrong place is invisible** when no forbidden dependency is involved. Behavior tests or specification-style tests of the rule itself cover that, and the guard does not.
- **A rule can be suppressed or deleted by the agent** unless something protects the guard files. Use `harness-permissions` and `harness-hooks` for that.
- **A known-violations list is debt.** It is only useful if someone shortens it.
- **A passing guard does not mean the architecture is good.** It means these rules hold.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. How to read the structure (modules, dependencies, libraries used)
3. The guard tool, how it matches names, and how to install it
4. The guard template, with the controls
5. Gradual adoption (known violations)
6. The command to run and how to read its result
7. How to plant a violation in a copy
8. Pitfalls and limits
9. Verified on (date, and what was not re-verified)
