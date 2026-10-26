# Specification notes for devcontainer-setup

Condensed from the official sources below. Use it to avoid re-reading everything, not as a replacement: when a property matters for a decision, check the current page.

Sources:

- `https://containers.dev/implementors/json_reference/` (property reference)
- `https://containers.dev/implementors/spec/` (discovery, lifecycle, merge logic)
- `https://containers.dev/implementors/features/` (Feature references and options)
- `https://containers.dev/supporting` (tools that implement the specification)
- `https://github.com/devcontainers/spec/tree/main/docs/specs` (`devcontainerjson-reference.md`, `devcontainer-lockfile.md`, `secrets-support.md`, `image-metadata.md`, `feature-dependencies.md`)
- `https://github.com/devcontainers/cli` (reference implementation)
- `https://github.com/devcontainers/templates` and `https://github.com/devcontainers/template-starter`

## 1. Discovery

Tools look, in order, for `.devcontainer/devcontainer.json`, `.devcontainer.json`, then `.devcontainer/<folder>/devcontainer.json` (one folder deep). Several may coexist; the tool must let the user choose.

## 2. Scenarios and their required properties

| Scenario | Required | Notes |
| --- | --- | --- |
| Image | `image` | Prebuilt image from a registry |
| Dockerfile | `build.dockerfile` (relative to `devcontainer.json`) | `build.context` defaults to `.`; also `build.args`, `build.target`, `build.cacheFrom`, `build.options` |
| Compose | `dockerComposeFile`, `service` | `runServices` limits what starts (default: all); later files override earlier ones; `workspaceFolder` defaults to `/` in this scenario, so set it |

`workspaceMount` overrides the default workspace mount and requires `workspaceFolder`. It should point at the repository root (where `.git` is); use `workspaceFolder` to select a sub-folder in a monorepo.

## 3. Lifecycle

Order: `initializeCommand` (host-side, may run more than once per session) → `onCreateCommand` → `updateContentCommand` → `postCreateCommand` → `postStartCommand` (every start) → `postAttachCommand` (every attach).

- `waitFor` selects the step tools wait for before connecting. Default `updateContentCommand`. The spec states `postCreateCommand` runs in the background by default, so a connected tool may see a container whose `postCreateCommand` has not finished; set `waitFor` when the next steps depend on it.
- A failed script skips the ones after it.
- Format: string (run through `/bin/sh`), array (no shell), object (named commands run in parallel; each must succeed).

## 4. Users and permissions

`containerUser` (user for all container operations; default is root or the last `USER` of the image), `remoteUser` (user for tools and sub-processes, such as terminals and tasks). `updateRemoteUserUID` (default `true`, Linux only) aligns the container user's UID/GID with the host user to avoid bind-mount permission problems; implementations may skip it when the engine already handles this.

## 5. Environment and variables

- `containerEnv`: static for the life of the container; changing it needs a rebuild.
- `remoteEnv`: applied to the tool's processes; prefer it when the value is not static. The reference implementation does not treat `remoteEnv` values as secrets.
- Substitution: `${localEnv:NAME}` (host variable; unset becomes blank), `${containerEnv:NAME}`, `${localWorkspaceFolder}`, `${containerWorkspaceFolder}`, `${devcontainerId}`. Defaults use `${localEnv:NAME:default}`; verify the exact form in the current reference before relying on it.
- Secrets: values do not belong in `devcontainer.json`; the specification expects tools to provide a secure input mechanism. The `secrets-support.md` page is partly the original proposal; check the CLI documentation for the implemented behavior before using a `secrets` mechanism.

## 6. Ports, mounts, privileges

- `forwardPorts` (union-merged), `portsAttributes`, `otherPortsAttributes`. `appPort` publishes ports and the application may need to listen on `0.0.0.0`, unlike a forwarded port.
- `mounts` uses the Docker CLI `--mount` syntax (string or object).
- `privileged` ("required for things like Docker-in-Docker, but has security implications"), `capAdd`, `securityOpt`, `init` (use tini).
- `hostRequirements` (`cpus`, `memory`, `storage`, `gpu`): the tool warns when not met.
- `shutdownAction`: `none`, `stopContainer` (default for image/Dockerfile), `stopCompose` (default for Compose).

## 7. Features

Reference forms: `<registry>/<namespace>/<feature>[:<version>]` (OCI; `latest` is implied without a version), `https://...tgz`, or `./path` relative to the folder with `devcontainer.json`. A string value is shorthand for the `version` option. Options become upper-case environment variables during install. `dependsOn` is a hard dependency; `installsAfter` is only ordering. `overrideFeatureInstallOrder` exists. Features can contribute `containerEnv`, `mounts`, `privileged`, `init`, `capAdd`, `securityOpt`, which are merged into the final configuration.

## 8. Lock file

`devcontainer-lock.json` lives beside `devcontainer.json` and pins Features: full version, resolved OCI reference with sha256 digest, integrity hash, and dependencies. Local Features are not recorded. The page does not say when it is written or whether to commit it; the CLI offers `--frozen-lockfile` (fail on drift) and `--no-lockfile` for `build` and `up`. Committing it is a recommendation of this skill, not a rule of the specification.

## 9. Merge logic (image metadata and Features into the final configuration)

Any true wins: `init`, `privileged`. Union: `capAdd`, `securityOpt`, `forwardPorts`. Collected into a list: `entrypoint`, `mounts` (last wins on conflict), all lifecycle commands. Max wins: `hostRequirements`. Last wins: `waitFor`, `containerUser`, `remoteUser`, `userEnvProbe`, `overrideCommand`, `shutdownAction`, `updateRemoteUserUID`. Per key, last wins: `remoteEnv`, `containerEnv`, `portsAttributes`. Left to tools: `customizations`.

## 10. CLI (reference implementation)

Commands seen in the repository README: `up`, `build`, `exec`, `read-configuration`, `features`, `templates`, plus `run-user-commands`, `outdated`, `upgrade`, `stop`, `down`. Install methods: install script (Linux and macOS, bundles Node.js), `npm install -g @devcontainers/cli` (needs Node.js, Python and a C/C++ toolchain), or from source. The README does not state Docker as a prerequisite explicitly, but the CLI builds and runs through the container engine. Run `devcontainer --help` for the installed version's commands and flags before depending on one.

`devcontainer templates apply --workspace-folder . --template-id ghcr.io/devcontainers/templates/<name>:<tag> --template-args '{...}' --features '[...]'` applies a Template (network, writes files).

## 11. Supporting tools

The specification is implemented by several tools with different coverage: VS Code (Dev Containers extension), the CLI, GitHub Codespaces (some limits, for example bind mounts are ignored except the Docker socket), JetBrains IDEs (early support), DevPod, Visual Studio (partial, C++ and CMake), and others. The configuration targets the specification; record which tool it was validated with.

## Verified on

2026-10-26, from the pages listed above, read through a summarizing fetch (not a byte-exact copy). Not re-verified: the exact default-value syntax of `${localEnv:NAME:default}`, the implemented behavior of `secrets`, whether `devcontainer down` and `stop` exist in the current CLI release, and the Template and Feature names (observed in the repositories on the same date; list them again when you need one).
