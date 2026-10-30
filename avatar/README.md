# AvatarKit

A self-contained layered avatar renderer and editor. No build step, no dependencies.
Copy this folder into any project.

| File | What it is |
|---|---|
| `avatar-kit.js` | Engine and editor (`window.AvatarKit`) |
| `parts.json` + `img/` | The parts: PNG layers plus colour ramps (made by `tools/canva_import.py`) |
| `demo.html` | Standalone test page |
| `tools/canva_import.py` | Turns Canva exports into `parts.json` + `img/` |

## Use it

```html
<script src="avatar/avatar-kit.js"></script>
<script>
  await AvatarKit.load('avatar/parts.json');

  // Profile picture (head and shoulders), 160px wide
  img.src = AvatarKit.toDataURL(config, { crop: true, size: 160, number: 7, captain: true });

  // Full body
  img.src = AvatarKit.toDataURL(config, { size: 400, body: 'goalie' });

  // Editor (full-screen overlay)
  AvatarKit.openEditor({ config, number: 7, captain: false, body: 'skater',
                         onSave: newConfig => save(newConfig) });
</script>
```

`config` is a small object you store per person, for example:

```json
{"v":2,"skin":"tan","hair":"mullet","hairColor":"ginger","facialHair":"full","facialHairColor":"ginger",
 "hat":"cap","hatColor":"red","glasses":null,"earring":null}
```

Unknown or missing values fall back to defaults, so old configs keep working when parts change.
`number`, `captain` and `body` are passed at render time, not stored in the config, because they come from the roster.
The editor only shows tabs for slots that have parts.

## Making parts in Canva

Every part is made by **editing a copy of one base image** in Canva and downloading it. Never move, resize or crop the image.

1. **`base.png`**: the bald, clean-shaven skater with the default face and a **blank sleeve** (no number; the app draws it).
   Use the same 500×500 framing as the original player art.
2. For each option, duplicate the base page, change only that one thing (e.g. Magic Edit → "short brown mullet"),
   and download it as PNG. Name it by type:

   | Type | File name | Notes |
   |---|---|---|
   | Skin tone | `skin_tan.png` | base with only the skin changed |
   | Hair | `hair_mullet.png` | make every hairstyle **brown**; other colours are generated |
   | Facial hair | `beard_full.png` | **brown** |
   | Hat | `hat_cap.png` | any one colour; other colours are generated |
   | Glasses / earring | `glasses_round.png`, `earring_gold.png` | |
   | Captain | `captain.png` | base with the captain's C on the chest |
   | Goalie | `goalie_base.png` | same bald player in goalie gear, head in the same spot |

3. Put them all in one folder and run:
   `python3 tools/canva_import.py <canva folder> .` (needs `pip install numpy pillow scipy`).

The script compares each image with `base.png` and keeps only what changed, so every part lines up exactly.
If something extra gets picked up, it's because the AI edit changed pixels outside the part. Redo that edit, or adjust `REGIONS` at the top of the script.

Colours: hair, facial hair and hats are recoloured by mapping the art's brightness onto a 5-step ramp (`ramps` in `parts.json`).
The colour the art was made in (`native`) is drawn untouched.
