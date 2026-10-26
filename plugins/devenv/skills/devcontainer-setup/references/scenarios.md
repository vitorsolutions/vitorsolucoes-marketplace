# Scenarios and patterns for devcontainer-setup

## 1. Choosing the scenario

| Situation | Scenario | Why |
| --- | --- | --- |
| Toolchain only (compiler, runtime, CLI tools), no dependent services | `image` plus Features | Least to maintain; the base image and Features are versioned upstream |
| Toolchain needs OS packages or setup that Features do not cover, or the project already has a container file for the application | `build` (Dockerfile) | Control over the image. If a production Dockerfile exists, a dedicated development stage (`build.target`) avoids a second source of truth, at the cost of coupling the development environment to production changes |
| Dependent services (database, cache, broker) | `compose` | Several services with health checks and dependency order. `runServices` limits what starts |
| The repository already has a Compose file for the app and its dependencies | `compose` extending or reusing it | Reuse the service definitions instead of copying them; keep the development Compose project separate (own `name`) so volumes and containers do not collide with the manual workflow |
| Docker commands are needed inside the environment (building images, running Compose from inside) | Any scenario plus the official Docker-in-Docker or Docker-outside-of-Docker Feature | Both have security costs: Docker-in-Docker typically needs `privileged`; Docker-outside-of-Docker gives the container control of the host engine. Require the user's explicit decision |

Prefer the closest official Template as the starting point and adjust it to the repository. Applying one with `devcontainer templates apply` uses the network and writes files, so ask first; otherwise write the equivalent files by hand after reading the Template's source in `github.com/devcontainers/templates`.

## 2. Image and Feature selection

- Base image: an official dev container base image or the runtime image the project already uses, with a pinned tag. Match the toolchain version the repository pins (SDK file, interpreter pin, engines field). If the repository pins nothing, say that the environment will define the version and ask which one.
- Features: add only what the base image lacks (a second runtime, a CLI, a shell utility). Pin a major version at minimum (`:1`), resolved from the Feature's current documentation at generation time. Features install in an order the tool computes; use `installsAfter` or `overrideFeatureInstallOrder` only when the order matters.
- Extensions: the minimum for the stack, under `customizations.<tool>`. The key names belong to the tool.

## 3. Lifecycle placement

| Work | Place |
| --- | --- |
| One-time setup of the container that does not depend on the sources | `onCreateCommand` |
| Dependency restore that must rerun when the sources or lock files change | `updateContentCommand` |
| Project setup after the user is assigned (tool restore, database migration for a development database, asset build) | `postCreateCommand` |
| Light work on every start (start a watcher, refresh a token) | `postStartCommand`, kept fast |
| Nothing slow | `postAttachCommand` |

Use one idempotent script in the repository (`scripts/` or `.devcontainer/`) instead of a long inline string. It should run twice without failing, use the locked install commands of the stack, and not require a TTY.

## 4. Patterns for Compose-based environments

These come from a real .NET project with a database and a frontend build, generalized. Apply a pattern only when its condition holds in the target repository.

- **Separate Compose project name** (`name:` in the file) so the development environment's containers and volumes do not clash with the repository's manual Compose workflow.
- **Reuse dependency definitions** with `extends` from the existing Compose file, then override what differs (for example `ports: !reset []` to avoid publishing the database to the host, `restart: "no"`). Check the Compose version in use supports `!reset` before using it.
- **The main service sleeps**: `command: sleep infinity` with `init: true`, since the tool attaches and runs the application itself.
- **Reuse the production Dockerfile** with a `dev` stage as `build.target` when one exists, with the same build context.
- **One published port, loopback only**: `127.0.0.1:${APP_DEV_PORT:-8080}:8080`, so the port is configurable and not exposed to the network.
- **Named volumes for heavy or platform-specific directories**: dependency folders with native binaries, the package cache, build output redirected to a path under the repository root when tests locate files relative to it. Handle their ownership in the setup script before first use, changing only the mount point.
- **Health checks and `depends_on: condition: service_healthy`** so the setup script does not race the database.
- **Development-only credentials**: defaults are throwaway values of a database that exists only inside the environment; real credentials (identity provider, third-party APIs) come from the host environment through `${VAR:-}` with an empty or non-functional default, and the README states that the related features do not work without them. Never put a working credential as a default.
- **Env example, not env**: `.env.example` with placeholders is tracked; `.env` is listed in `.gitignore`. Compose reads `.env` next to the Compose file automatically.
- **Locked installs in the setup script** (`restore --locked-mode`, `npm ci`, `uv sync --frozen`, or the stack's equivalent), with a stamp of the lock file hash to skip reinstalling when nothing changed.
- **Telemetry and noise off** for the toolchain through `containerEnv`, if the stack supports it.

## 5. Things to avoid

- Mounting `~/.ssh`, cloud credential folders or the Docker socket by default. Prefer the tool's agent forwarding for SSH and Git credentials, and mount only on an explicit request.
- Installing the project's dependencies in the Dockerfile with the sources copied in: the image then goes stale. Keep the image to the toolchain; restore in lifecycle commands.
- A `postCreateCommand` that downloads and executes scripts from the internet without a pinned version or checksum.
- Copying the production Dockerfile's runtime-only constraints (read-only filesystems, non-writable home) into the development stage.
- Disabling `updateRemoteUserUID` to silence a permission problem instead of fixing ownership.
