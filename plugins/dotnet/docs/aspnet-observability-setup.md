# ASP.NET Core Observability Setup

Adds vendor-neutral observability — structured logging, distributed tracing, and metrics via OpenTelemetry — to an existing ASP.NET Core project, detecting what's already wired up and only completing what's missing.

## What it is

Most ASP.NET Core projects either have no observability beyond console logging, or have it half-wired — a Serilog sink here, an `AddOpenTelemetry()` call there that only covers tracing but not metrics. This skill reads `Program.cs` and the `.csproj` first to understand what's already in place, then adds exactly the missing pieces: a structured logging bridge if none exists (or an OpenTelemetry bridge for an existing provider like Serilog, instead of replacing it), tracing and metrics instrumentation for ASP.NET Core, outgoing HTTP calls, EF Core when present, and the runtime itself, all exported via the OTLP protocol.

The stack is deliberately vendor-neutral. OTLP is the wire format every major observability backend accepts — Grafana Tempo/Loki, Jaeger, Datadog, Application Insights, and others — so this skill never locks a project into a specific vendor's SDK. It relies on the OpenTelemetry SDK's standard `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable instead of inventing a custom configuration key, and it never fabricates a real backend URL or credential — pointing the exporter at an actual backend is a deployment-time decision left to the user.

## When to use it

- An existing ASP.NET Core API has little or no observability and needs structured logging, tracing, and metrics added.
- A project has partial instrumentation (e.g., Serilog for logs only) and needs tracing/metrics added without disturbing what already works.

Not the right skill for scaffolding a brand-new project (see `minimal-api-scaffold`) or for diagnosing a specific slow query.

## What it guarantees

- **Detects existing instrumentation first** — never duplicates or rips out a logging/tracing/metrics setup that's already there; only completes what's missing.
- **Vendor-neutral by construction** — OpenTelemetry SDK + OTLP exporter throughout, compatible with any OTLP-speaking backend, never tied to one vendor's proprietary SDK.
- **No fabricated endpoints or credentials** — relies on the standard `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable (defaulting to `http://localhost:4317`), and always reports that a real backend still needs to be configured before telemetry is useful beyond a local machine.
- **Build-verified, not runtime-verified** — confirms the instrumentation code compiles via `dotnet build`; it doesn't start the application or require a live collector to be reachable.
