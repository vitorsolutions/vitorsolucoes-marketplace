# Devcontainer Setup

Assesses whether a repository and the developer's machine can run a Dev Container, reviews an existing configuration against the official specification, and creates or fixes one with confirmation. Agnostic to the stack and to the host operating system.

## Why this skill exists

A Dev Container gives every developer, and every agent, the same environment from the repository alone. It only works when the project can be built on Linux containers, its services can be containerized, and the machine has a container engine. Copying a configuration from another project hides those conditions. This skill checks them first and writes a configuration only when it makes sense.

## What it does

1. **Inventories** every configuration location defined by the specification and the container files around it.
2. **Reviews an existing configuration** (read-only): validity, scenario consistency, references that do not resolve, drift from the repository, lifecycle placement, users, secrets, ports, privileges, pinning, and cross-platform behavior. Findings are graded Observed, Hypothesis, Risk or Recommendation, with file and line.
3. **Assesses project fitness** when there is no configuration: *fit*, *fit with caveats*, *not fit* or *undetermined*, with evidence. A Windows-only application is reported as not fit, with alternatives, and nothing is written.
4. **Assesses the host** with read-only commands: container engine and Compose, architecture, resources, the Dev Container CLI. A missing component is reported as something to install, not as a reason to give up.
5. **Designs the smallest configuration** (image, Dockerfile or Compose scenario; Features; lifecycle commands), starting from the closest official Template.
6. **Previews every file**, writes after confirmation, and validates with the official Dev Container CLI: static read of the configuration, build and start (asked first), then the project's own build and tests inside the container.

## Sources of truth

The Development Container Specification and `containers.dev`, the Dev Container CLI, and the official Templates, Features and template starter repositories in the `devcontainers` GitHub organization. The skill keeps notes of what was verified and when, and prefers the current official page whenever they differ. Behavior that belongs to a tool (VS Code, Codespaces, JetBrains, DevPod) is labeled as such.

## Cross-platform

The configuration is checked for what breaks across Windows, macOS and Linux: line endings in scripts, host-side commands that assume a shell, absolute host paths, bind-mount cost for dependency folders, CPU architecture of base and service images, case sensitivity, and ports that collide.

## What it will not do

- Run an existing configuration before reading it. Host-side commands and Compose files execute on the developer's machine.
- Write secrets or defaults that authenticate anything. Credentials come from the host environment or an untracked `.env`.
- Enable `privileged`, mount the Docker socket, or publish ports beyond loopback without an explicit decision after stating the risk.
- Overwrite an existing configuration, or commit, push or stage anything.
- Containerize the application for production, set up CI, or author Templates and Features for others.

## When to use it

"Set up a devcontainer", "review our devcontainer.json", "can this project run in a dev container", "my devcontainer doesn't start on Windows".

## Limits

A passing build proves the environment on this host and architecture only. Features and base images float unless pinned, and the lock file covers Features, not the contents of the base image tag. Container engine behavior, file-sharing performance and licensing belong to the engine and the supporting tool, not to the specification. A Dev Container is not a security boundary against code the developer runs inside it.
