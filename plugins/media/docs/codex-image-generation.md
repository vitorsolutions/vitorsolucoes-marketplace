# Codex Image Generation

Generates and edits raster images from inside an agent session by driving the Codex CLI, using its built-in image tool and the sign-in and configuration the user already has. No OpenAI API key is used.

## Why this skill exists

Some coding agents cannot generate images. A developer who already has the Codex CLI signed in with a ChatGPT account has an image tool on the same machine, but calling it by hand means writing the request, finding the file, and moving it into the project. This skill does that, and keeps the parts that matter deterministic instead of leaving them to a second agent.

## Requirements

- Codex CLI installed, on `PATH`, and signed in through ChatGPT (`codex login`).
- The `image_generation` feature enabled, which is checked on each run.
- Python 3.9 or later.
- Pillow, only to produce an exact final size.

## What it does

1. **Settles the request**: subject, style, exact text, variations, size, and destination, asking only what changes the result.
2. **Checks the setup** before spending anything: CLI present, ChatGPT sign-in, feature enabled.
3. **Runs `codex exec`** in an empty temporary directory with a read-only sandbox, sending the request through standard input.
4. **Collects only this run's files** from the session folder under `$CODEX_HOME/generated_images/`, and verifies each one is a real PNG, JPEG, or WebP.
5. **Delivers without overwriting**: an existing name gets a `-v2` suffix, and the extension follows the real format.
6. **Resizes locally** when asked, scaling to cover and cropping the center, and warns about upscaling and cropped area.
7. **Looks at the result** and corrects it at most twice without asking.

It handles generation, variations, reference images, edits of existing pictures, and a final size.

## How the Codex session is used

| Aspect | Behavior |
|---|---|
| Sign-in | Proceeds only with a ChatGPT sign-in. An API key sign-in is refused, because it would bill the API |
| API key variables | `OPENAI_API_KEY` and `CODEX_API_KEY` are removed from the Codex process |
| Configuration | The user's model and `config.toml` apply as they are |
| Sandbox | Always `read-only`, the one setting the skill imposes |
| Disabled feature or unavailable tool | Reported; the skill does not enable it or switch to another route |

## What it will not do

- Call an image API, use an API key, or switch to another provider.
- Sign in or out, edit the Codex configuration, or install anything.
- Overwrite an existing file, including the picture being edited.
- Draw diagrams or charts that are better written as code.

## When to use it

"Generate an image of...", "make a cover for this article", "I need a logo concept", "swap the background of this photo", "create three banner variations at 1920x1080".

## Limits

- Each image counts against the plan's usage limits, and availability of the tool depends on the plan.
- The tool chooses the generated dimensions; an exact size is a local crop and resize, which can upscale.
- Edits regenerate the picture, so details outside the requested change can shift.
- Text inside images can come out misspelled and has to be checked.
- The sandbox restricts shell commands run by Codex. MCP servers configured in the user's Codex setup are still loaded during the run.
- Prompts and input images are sent to OpenAI under the user's account, and Codex keeps its own session history and generated files under `$CODEX_HOME`.
- If the configuration routes Codex to a different model provider, the skill does not override it, and image generation may not be available.
- Collecting files depends on where the CLI stores generated images, observed with Codex CLI 0.169.0. A future version that changes it makes the run report `no_image`.
