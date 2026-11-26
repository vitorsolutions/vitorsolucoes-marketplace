# Writing image requests

Describe the picture, not the tooling. Codex shapes the request for its image tool on its own, so
this is not a form to fill in: include the lines that remove ambiguity and leave out the rest.

## Order that works

1. **Purpose**: where the image will be used. It sets the level of finish.
2. **Subject**: what must be recognizable first.
3. **Setting**: where it is, or the kind of background.
4. **Style**: medium and treatment (editorial photo, flat vector look, isometric 3D, watercolor).
5. **Composition**: framing, viewpoint, placement, empty space reserved for later use.
6. **Light and color**: only when it matters; name the colors, with hex codes for brand colors.
7. **Exact text**: in quotes, with position and hierarchy.
8. **Exclusions**: what must not appear.

Concrete beats evaluative: "soft window light from the left, shallow depth of field" gives the model
something to do; "beautiful, high quality" does not.

## By type of piece

| Piece | State explicitly |
|---|---|
| Photo | Lens feel and distance, light source, time of day, real textures; "no illustration look" |
| Illustration | Medium, line weight, palette size, level of detail |
| Logo or icon concept | One idea, flat shapes, number of colors, plain background, legible when small |
| Interface mockup | Device, screen purpose, main regions, fidelity; keep visible text short |
| Infographic | Few blocks, reading order, every label verbatim |
| Banner or social post | Aspect ratio, headline verbatim, where text sits, margin around it |
| Transparent cutout | "Transparent background", full subject inside the frame, no cast shadow unless wanted |
| Texture or sprite | Seamless or isolated, view angle, grid and frame count for sheets |

Logo results are raster explorations. A final identity needs vector redrawing, and the user should
verify that it does not resemble an existing mark.

## Text inside images

- Quote it exactly and keep it short; error rates rise with length.
- Say that no other text should appear.
- Spell unusual names letter by letter.
- Check every character in the result. When the text must be exact and long, generate the picture
  without it and compose the text with code or a design tool.

## Edits

State the single change and then what stays:

```text
Replace the background with a plain light gray studio backdrop.
Keep the product, its label, proportions, edges, and lighting unchanged. Add no text.
```

Repeat the "keep" list on every new correction, because repeated edits drift. Edits regenerate the
whole picture, so fine details outside the requested change can differ from the original; compare
both. For pixel-exact changes, use an image editor.

With several input images, refer to them by number: "apply the palette of image 2 to the scene in
image 1".

## Size and aspect ratio

The built-in tool chooses its own dimensions; `--size` is applied afterwards by scaling and cropping
the center. When the target ratio is far from square (stories, wide headers), the script already
asks for a composition that survives the crop. Add "subject centered with generous margins" if a
result still gets cut, and prefer sizes close to what the tool produces to avoid upscaling.

## Variations

For `--n`, say what should differ ("three directions: geometric, hand drawn, typographic").
Without that, variations tend to be near duplicates.

## Example

```text
Purpose: header for a blog article about observability.
Subject: a lighthouse whose beam crosses a field of small abstract server shapes.
Style: flat illustration with subtle grain.
Composition: wide; lighthouse on the right third; left half calm, for a title added later.
Colors: deep navy, teal, one warm amber accent.
Exclusions: no text, no logos, no people.
```
