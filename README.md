# Mouse Config App

Small GUI tool that lets you configure what each mouse button does and generates
a ready-to-paste Logitech G HUB Lua script.

## Run
```
python3 app.py
```
(needs Python 3 with tkinter, which is standard on most installs)

## Supported action types
- **remap** — button sends a key or key combo (e.g. `lctrl,c`)
- **text** — button types out a saved string
- **combo** — button fires a sequence of keys with delays (e.g. `b,delay:150,1`)
- **toggle** — button starts/stops a repeating key press at a fixed interval

## Usage
1. Click **+ Add**, set the button number and action type, fill in the fields, click **Save this button**.
2. Repeat for each button you want to configure.
3. Click **Generate Script** to preview the Lua.
4. Click **Save As .lua**, then paste that file's contents into:
   G HUB → your mouse → Assignments → **+** → Script Editor.
5. Use **Save/Load config JSON** to keep your button setup for later editing.

## Not covered (not scriptable via G HUB Lua)
DPI switching, per-application profiles, and RGB lighting are configured
directly in G HUB's own UI (Point/Scroll tab, Applications, Lighting tab) —
there's no Lua API for them.

## Tests
```
python3 -m unittest test_generator.py -v
```
