# Stack mapping for devcontainer-setup

Markers identify the stack from files; they do not prove how the project is built or run. Read the project's own build and test commands before writing lifecycle commands. A repository can match several rows.

Official Templates and Features listed below were observed in `github.com/devcontainers/templates` and `github.com/devcontainers/features` on 2026-10-26. List the repositories again at generation time (the `src/` folder of each) and use the current names and options; do not trust this table for existence or version.

| Stack | Detection markers | Toolchain pin to match | Closest official Templates | Official Features that may apply | Project's own restore command (use the locked form) |
| --- | --- | --- | --- | --- | --- |
| .NET | `*.sln`, `*.slnx`, `*.csproj`, `global.json`, `Directory.Packages.props` | `global.json` | `dotnet`, `dotnet-postgres`, `dotnet-mssql`, `dotnet-fsharp` | `dotnet`, `node` (frontend build) | `dotnet restore --locked-mode` when lock files exist |
| Python | `pyproject.toml`, `requirements*.txt`, `uv.lock`, `poetry.lock`, `Pipfile` | `.python-version`, `requires-python`, tool settings | `python`, `anaconda`, `miniconda`, `anaconda-postgres` | `python` | `uv sync --frozen`, `poetry install --sync`, or `pip install -r` with hashes, per the lock in use |
| Node / TypeScript | `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `.nvmrc`, `tsconfig.json` | `.nvmrc`, `engines`, `packageManager` | `javascript-node`, `typescript-node`, `javascript-node-postgres`, `javascript-node-mongo` | `node` | `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable` |
| Go | `go.mod`, `go.sum`, `go.work` | `go` and `toolchain` lines in `go.mod` | `go`, `go-postgres` | `go` | `go mod download` |
| Java | `pom.xml`, `build.gradle(.kts)`, `gradlew`, `mvnw` | `maven.compiler.*`, Gradle toolchain, `.sdkmanrc` | `java`, `java-postgres` | `java` | `./mvnw` or `./gradlew` wrapper commands |
| Rust | `Cargo.toml`, `Cargo.lock`, `rust-toolchain(.toml)` | `rust-toolchain` | `rust`, `rust-postgres` | `rust` | `cargo fetch --locked` |
| PHP | `composer.json`, `composer.lock` | `require.php` | `php`, `php-mariadb` | `php` | `composer install` |
| Ruby | `Gemfile`, `Gemfile.lock`, `.ruby-version` | `.ruby-version` | `ruby`, `ruby-rails-postgres` | `ruby` | `bundle install --frozen` (verify flag for the Bundler version in use) |
| C / C++ | `CMakeLists.txt`, `Makefile`, `vcpkg.json` | Compiler requirements in the build files | `cpp`, `cpp-mariadb` | none specific | The project's build system |
| PowerShell | `*.ps1`, `*.psd1` | `#requires` lines, module manifests | `powershell` | `powershell` | `Install-PSResource` per project documentation |
| Other / generic | none of the above | Anything the repository documents | `debian`, `ubuntu`, `alpine`, `universal` | `common-utils`, `git`, `github-cli`, `azure-cli`, `terraform`, `kubectl-helm-minikube` | The project's documented setup |

Notes:

- The restore commands in the last column are the usual locked forms; confirm each against the project's own documentation and the installed tool's help before writing it into a script, and prefer the command the repository's CI already uses.
- Database Templates (`*-postgres`, `*-mssql`, `*-mariadb`, `*-mongo`) are Compose-based. Use them only when the repository really depends on that database, evidenced by connection settings, migrations or Compose files in the repository, not by a package name alone. Check the database image's published CPU architectures before recommending it for ARM hosts.
- `docker-existing-dockerfile` and `docker-existing-docker-compose` start from the repository's existing container files; consider them when the project already has them.
- `universal` is a large image meant for broad use. It is rarely the smallest configuration for one project.
- Windows-only stacks (.NET Framework, WPF, WinForms, COM, Windows services) match the .NET markers but fail the project fitness check; see `references/assessment.md`.
