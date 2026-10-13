# .NET stack reference for harness-reproducibility

## 1. Detection markers

`*.sln`, `*.slnx` (SDK 10 creates `.slnx` by default; `<solution>` in the commands below is the real file name), `*.csproj`, `global.json`, `Directory.Build.props`, `Directory.Packages.props`, `packages.lock.json`, `nuget.config`.

## 2. Toolchain pin: `global.json`

| Element | Detail |
| --- | --- |
| File | `global.json` at the repository root (or above the projects) |
| Create | `dotnet new globaljson --sdk-version <version> --roll-forward <policy>` |
| Content | `{ "sdk": { "version": "<version>", "rollForward": "<policy>" } }` |
| Read the effective version | `dotnet --version` run inside the repository |

Roll-forward policies decide how strict the pin is. `disable` accepts only the exact version, and the more permissive policies accept newer patch or feature bands. Pick with the user, using the trade-off in the skill. Use the version that `dotnet --version` reports today, not a newer or older one.

If the pinned SDK is not installed and the policy is `disable`, `dotnet` commands fail (exit `155` in the test). That is the intended behavior, so tell the user and the CI owner.

## 3. Dependency versions in one place: central package management

| Element | Detail |
| --- | --- |
| File | `Directory.Packages.props` at the repository root, created manually or with `dotnet new packagesprops` |
| Switch | `<ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>` |
| Versions | `<PackageVersion Include="..." Version="..." />` items in that file |
| Projects | `<PackageReference Include="..." />` with no `Version` attribute |

Adopting it requires removing `Version` attributes from every project. If any remains, restore fails with `NU1008` (exit `1` in the test). If two projects used different versions of the same package, you must choose one version, and that changes what one of them resolves: build and test afterwards, and say so.

## 4. Lock files

| Element | Detail |
| --- | --- |
| Enable | `<RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>` in each project, or in `Directory.Build.props` for all projects |
| Create | A normal restore writes `packages.lock.json` next to each project (needs the network and writes files) |
| Locked verification | `dotnet restore <solution> --locked-mode` |
| Read the result | Exit `0` when the lock matches. Exit `1` with `NU1004` when the project's dependencies no longer match the lock (both seen in the test). Any other error code (for example a source that cannot be reached) is a restore error, not a mismatch. |
| Caution | In the eval pass a restore with no `packages.lock.json` and no `RestorePackagesWithLockFile` also exited `0`, so a passing locked restore only protects projects that have lock files. Confirm they exist (section 5) |

Use the locked verification everywhere you only want to check. A plain restore can rewrite lock files when dependencies changed. Once a project has a lock file, restore uses it even if the property is not set, and having the lock file with the property set to `false` is a conflict that restore reports.

If a project uses central package management, transitive pinning and the lock file format depend on the NuGet version. Keep the SDK pinned so the format stays stable.

## 5. Checks that files are tracked and used

- `git ls-files "**/packages.lock.json" global.json Directory.Packages.props` lists what is tracked. It lists nothing for untracked or ignored files, so also run `git ls-files --others --ignored --exclude-standard -- "*packages.lock.json"` to find lock files that exist but are ignored (tested).
- `git check-ignore -v <file>` shows whether a rule ignores a file you expect to commit.
- Look in CI and in the agent guide for `--locked-mode`. A restore without it does not enforce the lock.

## 6. Pitfalls and limits

- **Restore needs the network** on a machine without a package cache. Ask first.
- **Implicit packages.** The SDK can add package references itself. A different SDK can change their versions and break a locked restore. Pin the SDK to avoid it.
- **Several package sources.** `nuget.config` can add feeds. Confirm which sources the lock was made against.
- **Warnings as errors and audit.** If failure on warning is on, vulnerability warnings from restore can fail it. That interacts with a lock file, which also hides fixes until refreshed.
- **Legacy projects** that use `packages.config` are not covered by these properties.
- **The lock does not pin the SDK.** Use `global.json` for that.

## 7. Verified on

2026-10-12, run in throwaway samples (SDK 10.0.401): `dotnet new globaljson` produced the expected file and `dotnet --version` reported the pinned version; a pin to an uninstalled SDK with `disable` made `dotnet` commands fail (exit `155`); with `RestorePackagesWithLockFile` set, restore created `packages.lock.json`; `dotnet restore --locked-mode` exited `0` unchanged and exited `1` with `NU1004` after a package version was changed in the project; central package management with a leftover `Version` attribute failed restore with `NU1008`. Microsoft Learn: central package management, locking dependencies with `packages.lock.json`, NuGet restore.

Not verified in this pass: multi-target projects, `nuget.config` source mapping, `RestoreLockedMode` as a property in CI, and migration of a real solution with conflicting package versions.

The ignored-lock-file command was run in a throwaway repository after the eval pass.
