# Assessment criteria for devcontainer-setup

Three read-only assessments plus the controls that make a configuration portable. Grade every finding **Observed** (seen in a file or command output), **Hypothesis** (plausible, not confirmed), **Risk** (consequence if it holds), or **Recommendation**. Do not turn a hypothesis into a fact because it is probable.

## 1. Conformance review (configuration present)

Read the configuration and everything it references. Check:

| # | Check | How |
| --- | --- | --- |
| 1 | Location and uniqueness | Which of the three discovery paths exist; if several, is that intentional and documented |
| 2 | Valid JSON with comments allowed; known property names | Compare to `references/spec-notes.md` and the current reference; unknown or misspelled properties are ignored silently, so they are findings |
| 3 | Scenario is coherent | Exactly one of `image`, `build`, `dockerComposeFile`+`service`; Compose scenario sets `workspaceFolder`; `runServices` lists real service names |
| 4 | References resolve | Every `build.dockerfile`, `build.context`, `dockerComposeFile`, `./` Feature path, script in a lifecycle command, `env_file` and mounted path exists, relative to the right base (`devcontainer.json` for devcontainer properties, the Compose file for Compose paths) |
| 5 | Drift from the repository | Toolchain version in the image vs the version the repository pins; ports vs what the app listens on; services vs the repository's own Compose or configuration; scripts and commands that no longer exist; extensions for tools the project no longer uses |
| 6 | Lifecycle placement | Install of the project's dependencies in `postCreateCommand` or `updateContentCommand`, not in `postStartCommand`; commands idempotent; `waitFor` set when later steps depend on a background `postCreateCommand`; no long work in `postAttachCommand` |
| 7 | Host-side commands | `initializeCommand` and Compose features run on the host; flag any shell-specific syntax (breaks on another OS), downloads, or writes outside the repository |
| 8 | Users | `remoteUser` is not root without a reason; ownership of named volumes mounted over the source tree handled (volumes start owned by root); `updateRemoteUserUID` not disabled without a reason |
| 9 | Secrets | No credential, token or password in any tracked file, including defaults in Compose files. Placeholders that cannot authenticate anything are acceptable if documented. `.env` ignored by git; `.env.example` present |
| 10 | Ports | Only the ports needed; published ports bound to loopback (`127.0.0.1:host:container`) unless remote access is intended; no database port published to the host without a reason |
| 11 | Privileges | `privileged`, `capAdd`, `securityOpt`, Docker socket mount, `--network=host` in `runArgs`: each needs a stated reason |
| 12 | Pinning | Image tag and Feature versions pinned to a version, not `latest` or an implicit latest; `devcontainer-lock.json` present and tracked, or its absence noted |
| 13 | Size of the configuration | Features, extensions and services the project does not use |
| 14 | Documentation | A short statement of how to open it and what the developer must supply (for example secrets); no contradiction with the files |
| 15 | Cross-platform controls | Section 4 below |

Report what is correct too, briefly, so the user knows what was checked.

## 2. Project fitness (no configuration)

Evidence comes from manifests, lock files, project files, Compose files, container files, CI definitions, scripts and configuration. Check each blocker class:

| Class | Blocks the container when | Evidence to look for |
| --- | --- | --- |
| Target platform | The code or its build is Windows-only (a Windows-only framework or desktop UI, COM, Windows services, Windows-only build tasks) | Target framework or platform in project files, native Windows dependencies, installer projects |
| Hardware and display | A GUI, a specific device, or GPU is required to run or test | Hardware access in code, `gpu` needs, device paths |
| Host-bound license or software | A required tool is licensed per host, cannot be installed on Linux, or needs an installer with a GUI | Documentation, build scripts |
| Services | A required service has no container option, or only for one CPU architecture | Connection strings, Compose services, documentation. Check the image's published platforms before promising support on ARM |
| Network and identity | The build needs a private feed, VPN-only registry, or internal certificate authority the container cannot reach or trust | Package sources, registry configuration, proxy settings. Not a blocker by itself: it changes the design (build secrets, proxy and CA configuration) |
| Size and resources | The environment needs more memory, CPU or disk than a developer machine typically offers | Documented requirements, large service stacks |
| Repository shape | The repository root is not where the workspace should open (monorepo), or several independent projects need different environments | Folder layout, multiple solutions or workspaces |

Also record what makes the project **easy** to containerize, because it shapes the design: a pinned toolchain, a lock file, an existing production container file, a documented setup script, a Compose file for dependencies, a test command that already runs headless.

Verdict wording: *fit*, *fit with caveats*, *not fit*, *undetermined*, each with the evidence. For *not fit*, give alternatives that do not require the container: the project's own documented setup, a Linux VM or WSL, or a remote development environment that provides the missing platform.

## 3. Host fitness (this machine)

Run only read-only commands. Pick the syntax for the shell in use. Never run `docker run`, `pull` or `build` here.

| Check | Command (shell-neutral unless noted) | Reads as |
| --- | --- | --- |
| Container engine installed and the daemon reachable | `docker version` | Both Client and Server sections must print. A client-only output means the daemon is not running or not reachable |
| Compose available | `docker compose version` | Needed for the Compose scenario |
| Engine details | `docker info` | OS type must be Linux containers (on Windows, not Windows containers); read the server architecture, CPU count, total memory |
| Disk | Windows PowerShell: `Get-PSDrive` for the drive that holds the engine data; Linux/macOS: `df -h` | Images and volumes need several GB; a Compose environment with a database more |
| Dev Container CLI | `devcontainer --version` | Missing is acceptable: offer to install or to validate manually |
| Editor / tool | The user says which tool they use (VS Code with the Dev Containers extension, JetBrains, CLI only, Codespaces). `code --list-extensions` lists VS Code extensions if the CLI `code` is available | The extension is a tool requirement, not part of the specification |
| Windows only | `wsl --status` and `wsl -l -v` | Whether WSL 2 is the engine backend is a property of the container engine's setup. Check its documentation rather than assuming |
| Line-ending policy | `git config core.autocrlf`, and read `.gitattributes` | See section 4 |
| Architecture | `docker info --format '{{.Architecture}}'` | Compare with the platforms the base image and service images publish |
| Network | Only if the user agrees: can the registries named in the configuration be reached | Do not probe unprompted |

Alternative engines (for example Podman or other Docker-compatible runtimes) can work with some tools but compatibility is specific to the tool and the engine. If the user uses one, say what is unverified rather than declaring it unsupported. Commercial licensing terms of a container engine are the organization's decision; mention that it may need a check, do not rule on it.

## 4. Cross-platform controls

A configuration committed to the repository must behave the same on Windows, macOS and Linux. Check, and fix when approved:

1. **Line endings.** Shell scripts and Dockerfiles run in Linux. With CRLF checked out on Windows they fail (`bad interpreter`, `\r: command not found`). Add rules to `.gitattributes` such as `*.sh text eol=lf`, and `Dockerfile* text eol=lf`, then tell the user that files already checked out may need renormalizing (`git add --renormalize .` stages changes; leave staging to the user). Show the diff first.
2. **No host shell assumptions.** `initializeCommand` and any host-side command must not use a shell syntax that exists on only one OS. Prefer no host-side commands at all. If one is unavoidable, use the array form with a program present on all three systems, or document the difference.
3. **No host paths.** No absolute paths such as `/home/...` or `C:\...` in `mounts`, Compose volumes, or `runArgs`. Use `${localWorkspaceFolder}`, relative paths in Compose, and named volumes. Host variables differ between systems (`HOME` on Unix, `USERPROFILE` on Windows); if a mount from the user's home is needed, make it optional and say what it needs on each system.
4. **Bind-mount cost.** Bind-mounted source is slower on some hosts (Windows and macOS, depending on the engine and file-sharing mode) for directories with many small files (dependency folders, build output). Put those directories on named volumes, and handle the ownership of the mount point (named volumes mounted over the source tree start owned by root). The performance of a given engine is a property of the engine; do not promise numbers.
5. **Architecture.** Developers may be on x86-64 or ARM64. Use multi-platform images and Features, and verify that each image the configuration pulls publishes both architectures (inspect the registry manifest with the engine's tooling, with permission). Where a service has no ARM image, say so and offer an alternative service or an emulation setting as a caveat, not a fix.
6. **Case sensitivity.** The container filesystem is case-sensitive while Windows and macOS checkouts usually are not. A project that references the same file with different casing builds on the host and fails in the container. Mention it when a build fails with a missing file.
7. **Ports.** Make the host port configurable by an environment variable with a default, so two projects, or two clones, can run side by side. Bind to loopback.
8. **Tool differences.** Do not rely on a property the target tool is documented not to support. If the repository declares Codespaces or another supporting tool as a target, check that tool's documentation for the properties used.
9. **Workspace location on Windows.** The documentation of the container engine and editor, not the specification, says where the clone should live for acceptable file performance. Tell the user to check it; do not state it as a rule.
