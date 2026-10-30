# AvatarKit

A self-contained pixel-art avatar renderer and editor. No build step, no dependencies.
Copy this folder into any project.

| File | What it is |
|---|---|
| `avatar-kit.js` | Engine and editor (`window.AvatarKit`) |
| `parts.json` | All body parts, face parts and colour ramps (~30 KB) |
| `demo.html` | Standalone test page |
| `tools/parts_png.py` | Convert parts to and from PNG so you can draw them in any image editor |
| `tools/build/` | The scripts that built the original parts from the team's player art (reference only) |

## Use it

```html
<script src="avatar/avatar-kit.js"></script>
<script>
  await AvatarKit.load('avatar/parts.json');

  // Profile picture (head and shoulders) as a PNG data URL
  img.src = AvatarKit.toDataURL(config, { crop: true, scale: 3, number: 7, captain: true });

  // Full body
  img.src = AvatarKit.toDataURL(config, { scale: 3, body: 'goalie' });

  // Editor (full-screen overlay)
  AvatarKit.openEditor({ config, number: 7, captain: false, body: 'skater',
                         onSave: newConfig => save(newConfig) });
</script>
```

`config` is a small object you store per person, for example:

```json
{"v":1,"skin":"light","eyes":"normal","eyeColor":"blue","brows":"thick","mouth":"grin",
 "hair":"mullet","hairColor":"brown","facialHair":"short","facialHairColor":"brown",
 "hat":null,"hatColor":"navy","glasses":null,"earring":null}
```

Unknown or missing values fall back to defaults, so old configs keep working when parts change.
`number`, `captain` and `body` are passed at render time, not stored in the config, because they come from the roster.

## How parts work

The canvas is 100×100. Every part is drawn in the exact position it sits on the body, so parts simply stack in the order listed in `parts.json` → `order`.

In each part's `rows`:

* `.` is transparent.
* `0`–`4` are shade levels (outline, shadow, mid, base, highlight). They're recoloured by the slot's colour ramp: hair colour, skin tone, eye colour, and so on. That's why each hairstyle exists once but comes in every colour.
* Any other character is a fixed colour from the part's `pal` list (eye whites, teeth, metal, the jersey).

## Adding or changing parts (e.g. drawn in Canva)

1. Export a guide: `python3 tools/parts_png.py export parts.json body skater body.png` (and `head default head.png`).
2. In your editor, make a 100×100 canvas (or 500×500, i.e. exactly 5×) with a transparent background. Put the guide PNGs on a locked layer underneath.
3. Draw the new part in place. For anything that should follow the player's chosen colour, use only these greys:
   `#000000` outline · `#404040` shadow · `#808080` mid · `#bfbfbf` base · `#ffffff` highlight.
   Use any other colour for fixed details.
4. Hide the guide layer and export a PNG with a transparent background. Turn anti-aliasing and smoothing off.
5. Import it: `python3 tools/parts_png.py import parts.json hair pompadour pompadour.png`

It appears in the editor straight away. Slots: `hair`, `facialHair`, `eyes`, `brows`, `mouth`, `hat`, `glasses`, `earring`, `body`.
To add colours, add a 5-step ramp (dark → light) under `ramps`.
