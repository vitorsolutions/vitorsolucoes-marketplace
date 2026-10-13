# .NET stack reference for harness-architecture-guard

## 1. Detection markers

`*.sln`, `*.slnx` (SDK 10 creates `.slnx` by default, and every `dotnet sln` command below accepts it), `*.csproj`. A guard needs at least two projects (or one project that must stay free of a library). Legacy projects without an SDK reference are not covered.

## 2. Reading the structure

| Need | Command |
| --- | --- |
| Projects in the solution | `dotnet sln <solution> list` |
| Project references of each project | `dotnet list <project> reference` |
| Assembly and root namespace names | `dotnet msbuild <project> -getProperty:AssemblyName,RootNamespace` (MSBuild 17.8 or later). Both defaulted to the project name in the sample. |
| Libraries a project uses | `dotnet list <project> package` |

Build the direction map from the reference graph, never from project names. A project called "Domain" can still reference an outer project, and a project that references nothing may still use a library type.

The compiler already rejects a circular project reference. So wrong-direction project references that remain possible are the ones that do not form a cycle, and the more common leak is a type-level dependency on a library or on a namespace that the project can see through another reference. That is what the guard below detects.

## 3. The guard tool

`NetArchTest.Rules` (a NuGet package) inspects compiled types and reports which types depend on which namespaces or types. Version 1.3.2 was used in the sample. Add it with `dotnet add <test project> package NetArchTest.Rules` and read the version it resolves, because the current version can differ.

Name matching (observed):

- A dependency name matches at a **segment boundary**: the exact namespace (`Shop.Application`), a parent namespace (`Shop`), and a full type name (`Shop.Application.PlaceOrder`) all matched.
- A partial segment (`Shop.Appl`) and a lookalike sibling namespace (`Shop.ApplicationExtras`) did **not** match.
- A name that matches nothing makes a `ShouldNot` rule pass. See the pitfalls.

## 4. The guard template

Create a new test project, named after the solution with the suffix `.ArchTests`, in the folder where the solution keeps its tests. Use the test framework that the repository already uses (xUnit was used in the sample). Reference every layer project from it, so the assemblies are copied to its output, and load them by name so that no marker type has to be added to production code.

```csharp
using System.Reflection;
using NetArchTest.Rules;
using Xunit;

namespace <Root>.ArchTests;

public class ArchitectureTests
{
    private const string Domain = "<Root>.Domain";
    private const string Application = "<Root>.Application";
    private const string Infrastructure = "<Root>.Infrastructure";

    private static Assembly Load(string name) => Assembly.Load(new AssemblyName(name));

    // Compares the failing types of a rule with the violations the team already knows about.
    // New violations fail. Known violations that no longer fail also fail, so the list can only shrink.
    private static void Check(TestResult result, params string[] knownViolations)
    {
        var failing = (result.FailingTypeNames ?? []).ToHashSet();
        var unexpected = failing.Except(knownViolations).OrderBy(x => x).ToList();
        var stale = knownViolations.Except(failing).OrderBy(x => x).ToList();
        Assert.True(unexpected.Count == 0, "New violations: " + string.Join(", ", unexpected));
        Assert.True(stale.Count == 0, "Known violations that no longer fail, remove them from the list: " + string.Join(", ", stale));
    }

    // ---- Guards: keep the rules from passing because they looked at nothing ----

    [Theory]
    [InlineData(Domain)]
    [InlineData(Application)]
    [InlineData(Infrastructure)]
    public void Layer_assembly_has_types(string assembly)
        => Assert.NotEmpty(Types.InAssembly(Load(assembly)).GetTypes());

    [Theory]
    [InlineData(Application)]
    [InlineData(Infrastructure)]
    public void Forbidden_target_namespace_exists(string ns)
        => Assert.NotEmpty(Types.InAssemblies([Load(Domain), Load(Application), Load(Infrastructure)])
            .That().ResideInNamespace(ns).GetTypes());

    [Fact]
    public void Positive_control_the_scan_can_see_a_real_dependency()
        => Assert.True(Types.InAssembly(Load(Application)).That().ResideInNamespace(Application)
            .Should().HaveDependencyOn(Domain).GetResult().IsSuccessful);

    // ---- Rules (one test per rule the user approved) ----

    [Fact]
    public void Domain_does_not_depend_on_outer_layers()
        => Check(Types.InAssembly(Load(Domain)).ShouldNot().HaveDependencyOnAny(Application, Infrastructure).GetResult());

    [Fact]
    public void Application_does_not_depend_on_infrastructure()
        => Check(Types.InAssembly(Load(Application)).ShouldNot().HaveDependencyOn(Infrastructure).GetResult());

    [Fact]
    public void Domain_does_not_depend_on_http()
        => Check(Types.InAssembly(Load(Domain)).ShouldNot().HaveDependencyOn("System.Net.Http").GetResult());
}
```

After creating the project, register it in the solution (`dotnet sln <solution> add <guard project>`), after asking, since that edits the solution file. Observed: a guard project that is not in the solution is skipped by `dotnet test <solution>` and nothing reports it, because the existing test project still runs and passes.

Adjust the layers and the rules to what the user confirmed. Notes on the template:

- **Positive control.** `Should().HaveDependencyOn` applies to **every** type in the set. Narrow the set with `That().ResideInNamespace(...)`, and make sure no type that lacks the dependency is in it. A freshly generated class library contains a placeholder class (`Class1`) that breaks this control. Remove placeholders only with the user's approval, since they are production files.
- **Libraries outside the solution** (for example `System.Net.Http` or an ORM namespace) cannot be checked with the existence guard. Prove them with the planted violation (section 7).
- Keep the placeholder test that the test template generates out of the guard project, or replace it. It asserts nothing.

## 5. Gradual adoption

Put the full names of the types that already break a rule in the extra arguments of `Check(...)` for that rule. The sample showed all four cases: a stale entry fails, a listed type passes, a new violation fails with its name, and a misspelled layer name fails the existence guards.

## 6. Command and result

`dotnet test <solution> --logger "trx;LogFileName=<name>.trx" --results-directory <temporary directory>` (or run only the guard project). Read the exit status and the `Counters` element of the TRX file. A run with `total="0"` or a missing TRX is a guard that checked nothing. Also check that the `testName` entries of the TRX include the guard's tests, or that the count equals the number of checks you wrote (nine in the sample below), because `total` alone is satisfied by the other test project. Each test project can write its own result file, so read the one of the guard project, or give each a distinct `LogFileName`. Text output is localized, so do not parse it.

A failing rule reports the failing type name, and the message names it in the test result.

## 7. Planting a violation in a copy

1. Copy the solution folders to a temporary directory, without `bin`, `obj`, `.git`, and package folders.
2. In the copy, add a new file in the inner project that uses a forbidden type, for example a class that has a field of `System.Net.Http.HttpClient` in the domain project.
   - **Layer rule.** Do not add a reference from the inner project to the outer one: the outer project already references the inner one, and the build stops with a circular reference error (MSB4006). Instead, create a tiny class library in the copy that declares one type in the forbidden namespace (for example `namespace <Root>.Infrastructure;` with `class PlantedType {}`), reference it from the inner project, and add a class in the inner project that has a field of that type. That project does not reference anything back, so there is no cycle, and the guard matches the type by its namespace.
   - If neither works, report the layer rule as written but not proven.
3. Run the guard in the copy. Expect exit `1`, and the failing rule naming the planted type, with the other rules still passing. If the planted type sits in the application namespace and does not use a domain type, the positive control also fails, because it requires a real dependency in every type of that set: make the planted class use a domain type too, or expect and ignore that one failure.
4. Delete the copy.

In the sample, a planted `HttpClient` field in the domain failed exactly the HTTP rule and named the type. A planted type in a tiny project in the infrastructure namespace, used by the domain, failed exactly the domain-direction rule (`New violations: <Root>.Domain.Leak`) while the application rule still passed.

## 8. Pitfalls and limits

- **A misspelled forbidden name passes forever.** The guards in section 4 cover names that belong to the solution. Names outside it need the planted proof.
- **Segment matching.** A partial name does not match, so write whole namespaces or types.
- **`Should` is universal.** A positive control that includes any unrelated type fails.
- **Project references nobody uses** leave no type dependency and are not seen. A reference check on the project files would catch them. That was not exercised here.
- **Compiler-generated types** exist in the scanned set. They normally follow the dependencies of the code that produced them.
- **Test project must reference every layer** or the assemblies fail to load by name.
- The tests can be edited or deleted by the agent. Protect the guard project with permission rules.

## 9. Verified on

2026-10-12, run in throwaway samples (SDK 10.0.401, NetArchTest.Rules 1.3.2, xUnit template): the clean guard passed with all checks counted in the TRX; a planted `HttpClient` use in a copy failed exactly the HTTP rule and named the type; a rule on a namespace with no types passed silently; the name-matching cases in section 3; loading assemblies by name without marker types; the four known-violation cases; and a misspelled layer name failing the existence guards.

Also verified on the same date: a guard project left out of the solution is skipped by `dotnet test` of the solution (the TRX listed only the existing test), registering it with `dotnet sln add` made the run report nine guard tests, and the shim-project proof for a layer rule.

Not verified in this pass: other test frameworks, other NetArchTest versions, ArchUnitNET, project-reference checks on the project files, and solutions with many layers or multi-targeting.
