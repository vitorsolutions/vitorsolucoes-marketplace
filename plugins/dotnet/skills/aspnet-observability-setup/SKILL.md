---
name: aspnet-observability-setup
description: >
  Adds vendor-neutral observability (structured logging, distributed tracing, and metrics via
  OpenTelemetry) to an EXISTING ASP.NET Core project, detecting what's already wired up and only
  completing what's missing. Use this whenever the user asks to "add observability", "set up
  tracing/logging/metrics", "instrument this API with OpenTelemetry", "adiciona observabilidade nessa
  API", "configura tracing/OTel nesse projeto", or wants their ASP.NET Core app to export telemetry
  without committing to a specific backend (Grafana, Jaeger, Datadog, Application Insights, etc. all
  consume OTLP the same way). Never assumes a project has zero instrumentation — always reads
  Program.cs and the .csproj first to detect existing logging providers (e.g. Serilog) or
  OpenTelemetry registration, and bridges into or extends what's there instead of duplicating or
  ripping it out. Do NOT use this skill to scaffold a brand-new project from scratch (see the
  minimal-api-scaffold skill for that) or to diagnose a specific slow query (see an EF Core
  performance skill for that). Only validates the result with `dotnet build` — it does not run the
  application or require a live telemetry backend to be available.
---

# ASP.NET Core Observability Setup

## Your role

You are adding observability to a project that already exists and already runs — this is an additive, incremental change, not a scaffold. Treat whatever is already there as something to understand and extend, not something to overwrite. A project that already has Serilog wired for logging doesn't need Serilog ripped out in favor of something else; it needs its output bridged into the same telemetry pipeline as tracing and metrics.

The stack is OpenTelemetry end to end, specifically because it's vendor-neutral: the OTLP exporter this skill wires in works identically whether the user's backend ends up being Grafana + Tempo + Loki, Jaeger, Datadog, Application Insights, or anything else that speaks OTLP. Never hardcode a specific backend's SDK or a specific vendor's exporter package — that decision belongs to the user's infrastructure, not to this skill.

## Step 1 — Detect what's already instrumented

Before adding anything, read:

1. The project's `.csproj` — look for `OpenTelemetry*` packages already referenced, `Serilog*` packages, or any other logging/tracing package (`Microsoft.ApplicationInsights`, `NLog`, etc.).
2. `Program.cs` — look for an existing `AddOpenTelemetry()` call and what it already configures (`.WithTracing(...)`, `.WithMetrics(...)`, logging provider registration), and for existing logging setup (`UseSerilog()`, `builder.Logging.Add...`).
3. Any other project references that imply what instrumentation packages are relevant — e.g., if the project references `Microsoft.EntityFrameworkCore`, EF Core's own OpenTelemetry instrumentation source is worth adding to tracing; if it calls out to other HTTP APIs via `HttpClient`, HTTP client instrumentation is worth adding.

Build a short mental (and later, reported) list: what's already there for logging / tracing / metrics, and what's missing. Everything from here on only adds the missing pieces — never re-register something already configured.

## Step 2 — Wire logging

- **If a structured logging provider already exists** (Serilog is the common case): don't replace it. Add the appropriate OpenTelemetry sink/bridge for that provider (e.g., `Serilog.Sinks.OpenTelemetry` for Serilog) so its output flows into the same OTLP pipeline as tracing and metrics, instead of running two disconnected telemetry systems.
- **If no structured logging provider exists**: wire OpenTelemetry directly into `Microsoft.Extensions.Logging` via `builder.Logging.AddOpenTelemetry(...)`, including `IncludeFormattedMessage` and `IncludeScopes` so log output stays readable and scoped values aren't dropped.

## Step 3 — Wire tracing and metrics

Add the OpenTelemetry SDK and instrumentation packages that are actually missing (via `dotnet add package`, never re-adding what Step 1 already found present):

- `OpenTelemetry.Extensions.Hosting` — the hosting integration (`AddOpenTelemetry()` on `IServiceCollection`).
- `OpenTelemetry.Instrumentation.AspNetCore` — incoming request tracing/metrics.
- `OpenTelemetry.Instrumentation.Http` — outgoing `HttpClient` call tracing/metrics, if the project makes outbound HTTP calls.
- `OpenTelemetry.Instrumentation.EntityFrameworkCore`, only if Step 1 found an EF Core reference — traces query execution.
- `OpenTelemetry.Instrumentation.Runtime` — process-level metrics (GC, thread pool, etc.), cheap to add and broadly useful.
- `OpenTelemetry.Exporter.OpenTelemetryProtocol` — the OTLP exporter, the vendor-neutral wire format every major backend accepts.

In `Program.cs`, configure a `ResourceBuilder` with the service name set from the assembly/project name — telemetry without a service name shows up as `unknown_service` in any backend, which defeats the point. Then:

```csharp
builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r.AddService(serviceName: builder.Environment.ApplicationName))
    .WithTracing(t => t
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        // .AddEntityFrameworkCoreInstrumentation() — only if EF Core is present
        .AddOtlpExporter())
    .WithMetrics(m => m
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .AddOtlpExporter());
```

Don't hardcode a specific OTLP endpoint in code or in `appsettings.json`. The OpenTelemetry .NET SDK already honors the standard `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable (defaulting to `http://localhost:4317` if unset) — rely on that convention rather than inventing a custom configuration key, so the project stays consistent with how every other OTel-instrumented service (in any language) is configured. Mention this default explicitly in the final report so the user knows where to point it.

## Step 4 — Validate

Run `dotnet build`. This skill does not start the application or require a live collector/backend to be reachable — it only confirms the instrumentation code compiles. If the user wants to confirm telemetry is actually flowing, that's a separate, explicit ask (e.g., running a local OTel collector), not something this skill does on its own.

## Step 5 — Report

State clearly, for each of logging/tracing/metrics:

- What was already present and left untouched.
- What was added.
- That the OTLP endpoint defaults to `http://localhost:4317` via the standard `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable, and needs to point at a real collector/backend before telemetry is actually usable anywhere beyond a local machine.

Never invent a real backend URL, API key, or vendor-specific connection string — if the user names a specific backend they want to send data to, that's a follow-up configuration step for them, not something this skill fabricates.
