# Manic EMU skin format: working notes

What follows was worked out by building and play-testing many skins. It is not official documentation, so test on your own device and Manic version (written against Manic 2.0.2).

## The file
A `.manicskin` is a plain zip. At the top level it holds `info.json`, one background image per orientation (`portrait.png`, `landscape.png`), and the control artwork as PDFs (`btn-0.pdf`, `thumbstick.pdf`, `dpad.pdf`...).

## info.json
- Top level: `name`, `identifier` (must be unique per skin), `gameTypeIdentifier`, `representations`.
- `representations` > device (`iphone` / `ipad`) > mode (`edgeToEdge` / `standard`) > orientation (`portrait` / `landscape`).
- Each orientation has `assets.large` (the background), `mappingSize` (the canvas size in points), `screens` (where the game is drawn, `outputFrame`) and `items` (the controls).
- Each item has a `frame` (x, y, width, height in canvas points), `inputs`, optional `asset.normal` (the artwork PDF) and optional `extendedEdges` (extra touch area around the frame).
- A thumbstick item uses `thumbstick: {name, width, height}` instead of `asset`, and its inputs map to `leftThumbstickUp/Down/Left/Right`.
- A D-pad item has the four inputs `up/down/left/right`.
- Utility buttons use `menu`, `quickLoad`, `quickSave`, `start`, `select`, `toggleFastForward`.
- Items without artwork are invisible but still take touches. The "arms" trick for D-pads uses this: single-input invisible items around the D-pad give reliable up/down/left/right.

## Face button numbering (Manic 2.0.2)
Manic assigns the arcade buttons by how many buttons a skin has:

| Buttons | Inputs, in reading order |
|---|---|
| 1 | b |
| 2 | b a |
| 3 | b a y |
| 4 | b a / y x |
| 5 | b a y / x l1 |
| 6 | b a y / x l1 r1 |

Top row first. Fighting games like Tekken 3 map these as LP, RP, LK, RK for a 4-button skin; other games differ, so test.

## Left-handed skins
Mirror the main layout so the stick/D-pad moves to the right and the action buttons move to the left, while keeping the labels inside each button group in their usual left-to-right reading order (`LOAD` / `SAVE`, `START` / `FF`). In landscape, those small utility groups swap sides to follow the mirror; in portrait, they stay in their standard positions.


## Combo buttons
A button may have several inputs (`["b", "y"]`) and presses them together. Never rename inputs positionally on a skin with combos, because it breaks the multi-input buttons. Rebuild them from the action you want instead.

## Canvas and touch areas
- Controls should sit inside the canvas. A few points of `extendedEdges` overhang at the screen edge is harmless.
- Keep `extendedEdges` modest so neighbouring buttons do not steal each other's touches.

## Checking your work
- `check_skin.py`: structure, missing files, bad inputs, off-canvas controls, duplicate identifiers.
- `contact_sheet_easy.py`: draws many skins side by side so you can eye-check colour and spacing. The automatic checks cannot see a dark button on a dark background.
