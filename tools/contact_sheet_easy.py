#!/usr/bin/env python3
"""contact_sheet_easy.py: draw skins into picture sheets so you can EYE-CHECK many layouts at once.

The checkers cannot see colour problems (e.g. dark pills on a light skin). This draws, for every layout, the same colourway(s)
side by side (landscape + portrait), with the real stick / D-pad / button artwork on top of the background image,
and the game screen shown as grey. Look down a column: every layout of one colourway should look like family.

    python contact_sheet_easy.py PATH [PATH ...] [options]

PATH   a folder (searched recursively), a release .zip (zips inside zips are fine) or a single .manicskin / .deltaskin
       (Manic EMU and Delta skins both work; no PATH = the current folder)
Options
  --colours "all"   which colourways to draw (default: all; names as in the skin file names)
  --orient both|landscape|portrait  default both
  --rows 4                          layouts per picture (default 4); more layouts = more pictures
  --width 400                       width in pixels of each landscape tile (default 400); every tile is fitted in a box, so iPad skins are no longer cut off
  --out contact_sheets              folder for the pictures (created if missing)
  --mode edgeToEdge|standard        which Delta/Manic layout to draw when a skin has both (default: edgeToEdge, else standard)
  --boxes                           outline every touch area and label it with its input (handy for Delta skins, whose buttons are
                                    painted into the background so there is no separate button artwork to draw)
  --compact                         (always on for a PATH with many colourways; shown for completeness) leave out 'missing' tiles: each row shows only the colourways that exist for that layout,
                                    with the colour name above each tile (good for mixed folders of different layouts and colours)

Examples
  python contact_sheet_easy.py .                                          (everything under the current folder, all)
  python contact_sheet_easy.py "C:\\skins\\Twin Stick" --colours "The Skins Color name eg. Nightfall Purple"
  python contact_sheet_easy.py newset.zip --colours all --rows 2          (every colourway: big output, use few layouts)

Needs Pillow. Controls are drawn with the first of: PyMuPDF (pip install pymupdf), the pdftocairo program, or, if neither
is found, plain outlines (backgrounds, pills and coin boxes are still real; only stick/button artwork is outlined).
It never changes your skins.
"""
import sys, os, io, re, json, zipfile, shutil, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

COLOURS = arg('--colours', 'all')
ORIENT = arg('--orient', 'both')
ROWS = int(arg('--rows', 4))
LW = int(arg('--width', 400))
OUT = arg('--out', 'contact_sheets')
COMPACT = '--compact' in sys.argv or COLOURS.lower() == 'all'    # a grid of 20+ colourways would be thousands of pixels wide
MODE = arg('--mode', 'edgeToEdge'); BOXES = '--boxes' in sys.argv
if '-h' in sys.argv or '--help' in sys.argv:
    print(__doc__); sys.exit(0)
paths, skip = [], False
for a in sys.argv[1:]:                                     # everything that is not an option (or an option's value) is a PATH
    if skip: skip = False; continue
    if a in ('--colours', '--orient', '--rows', '--width', '--out', '--mode'): skip = True; continue
    if a.startswith('--'): continue
    paths.append(a)
if not paths:
    paths = ['.']
EXTS = ('.manicskin', '.deltaskin')

# ---------- collect skins (name, bytes) from folders / zips / .manicskin ----------
def is_skin(data):
    try: return 'info.json' in zipfile.ZipFile(io.BytesIO(data)).namelist()
    except Exception: return False
skins = []
def add_zip(label, data):
    try: z = zipfile.ZipFile(io.BytesIO(data))
    except Exception: return
    for n in z.namelist():
        if n.endswith('/') or '__MACOSX' in n: continue
        if n.lower().endswith(EXTS): skins.append((os.path.basename(n), z.read(n)))
        elif n.lower().endswith('.zip'): add_zip(n, z.read(n))
for p in paths:
    if os.path.isdir(p):
        for root, _, files in os.walk(p):
            if os.path.abspath(root).startswith(os.path.abspath(OUT)): continue   # never re-read our own output
            for f in files:
                fp = os.path.join(root, f)
                if f.lower().endswith(EXTS): skins.append((f, open(fp, 'rb').read()))
                elif f.lower().endswith('.zip'): add_zip(f, open(fp, 'rb').read())
    elif p.lower().endswith('.zip'): add_zip(p, open(p, 'rb').read())
    elif p.lower().endswith(EXTS): skins.append((os.path.basename(p), open(p, 'rb').read()))
if not skins: sys.exit('No .manicskin or .deltaskin files found.')

def split(fn):
    base = os.path.splitext(fn)[0]
    return tuple(base.rsplit(' - ', 1)) if ' - ' in base else (base, '?')
want = None if COLOURS.lower() == 'all' else [c.strip().lower() for c in COLOURS.split(',') if c.strip()]
cols_present = sorted({split(f)[1] for f, _ in skins})
chosen = [c for c in cols_present if want is None or c.lower() in want]
if not chosen: sys.exit('None of those colourways were found. Colourways present: ' + ', '.join(cols_present))
if want:   # keep the order the user typed
    chosen.sort(key=lambda c: want.index(c.lower()))
by = {}
for f, d in skins:
    lay, col = split(f)
    if col in chosen: by.setdefault(lay, {})[col] = d
layouts = sorted(by, key=lambda s: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)])

# ---------- PDF drawing: PyMuPDF > pdftocairo > outline ----------
try:
    import pymupdf as fitz; HAVE_FITZ = True        # current PyMuPDF name
except ImportError:
    try:
        import fitz; HAVE_FITZ = True               # older PyMuPDF
    except Exception: HAVE_FITZ = False
except Exception: HAVE_FITZ = False
CAIRO = shutil.which('pdftocairo')
WARNED = []
def pdf_img(data, w, h):
    w, h = max(int(round(w)), 2), max(int(round(h)), 2)
    if HAVE_FITZ:
        try:
            page = fitz.open(stream=data, filetype='pdf')[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(w / page.rect.width, h / page.rect.height), alpha=True)
            return Image.frombytes('RGBA', (pix.width, pix.height), pix.samples)
        except Exception: pass
    if CAIRO:
        try:
            with tempfile.TemporaryDirectory() as td:
                open(os.path.join(td, 'a.pdf'), 'wb').write(data)
                subprocess.run([CAIRO, '-png', '-transp', '-singlefile', '-scale-to-x', str(w), '-scale-to-y', str(h),
                                os.path.join(td, 'a.pdf'), os.path.join(td, 'o')], check=True, capture_output=True)
                return Image.open(os.path.join(td, 'o.png')).convert('RGBA')
        except Exception: pass
    if not WARNED:
        WARNED.append(1); print('Note: no PDF renderer found (pip install pymupdf). Stick/button artwork is drawn as outlines.')
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse((1, 1, w - 2, h - 2), outline=(255, 80, 80, 255), width=2); return im

def rep_of(info, orient):
    """The layout to draw: iPhone before iPad, and the requested --mode (default edgeToEdge) before the others."""
    devs = sorted(info['representations'].items(), key=lambda kv: kv[0] != 'iphone')
    for dname, dev in devs:
        for mname in sorted(dev, key=lambda m: m.lower() != MODE.lower()):
            if orient in dev[mname]: return dev[mname][orient]
    return None

def bg_name(assets):
    """Manic skins use 'large'; Delta skins may use 'Large'/'large', or only 'resizable', 'medium' or 'small'."""
    low = {k.lower(): v for k, v in assets.items()}
    for k in ('large', 'medium', 'small', 'resizable'):
        if k in low: return low[k]
    return next(iter(assets.values()))

def asset_img(z, name, w, h):
    """Buttons and sticks are PDFs in Manic skins and can be PNGs in Delta skins."""
    if name.lower().endswith('.pdf'): return pdf_img(z.read(name), w, h)
    return Image.open(io.BytesIO(z.read(name))).convert('RGBA').resize((max(2, round(w)), max(2, round(h))), Image.LANCZOS)

def render(data, orient, box=None):
    z = zipfile.ZipFile(io.BytesIO(data)); info = json.loads(z.read('info.json')); rep = rep_of(info, orient)
    if rep is None: return None
    bg = Image.open(io.BytesIO(z.read(bg_name(rep['assets'])))).convert('RGBA')
    s = bg.width / rep['mappingSize']['width']
    canvas = Image.new('RGBA', bg.size, (118, 118, 128, 255)); canvas.alpha_composite(bg)   # grey where the game shows through
    cache = {}; box_items = []
    for it in rep['items']:
        fr = it['frame']
        if BOXES:
            e = it.get('extendedEdges') or {}
            box_items.append((fr['x'] - e.get('left', 0), fr['y'] - e.get('top', 0), fr['x'] + fr['width'] + e.get('right', 0), fr['y'] + fr['height'] + e.get('bottom', 0),
                              it['inputs'] if isinstance(it['inputs'], list) else list(it['inputs'].values())))
        if 'thumbstick' in it:
            name = it['thumbstick']['name']; w, h = it['thumbstick']['width'] * s, it['thumbstick']['height'] * s
            x, y = (fr['x'] + fr['width'] / 2) * s - w / 2, (fr['y'] + fr['height'] / 2) * s - h / 2
        elif (it.get('asset') or {}).get('normal'):
            name = it['asset']['normal']
            if name == 'blank.pdf': continue                       # invisible D-pad arm
            w, h = fr['width'] * s, fr['height'] * s; x, y = fr['x'] * s, fr['y'] * s
        else: continue
        if name not in z.namelist(): continue
        key = (name, round(w), round(h))
        if key not in cache: cache[key] = asset_img(z, name, w, h)
        canvas.alpha_composite(cache[key], (int(round(x)), int(round(y))))
    if BOXES:
        dr = ImageDraw.Draw(canvas); fnt = font(max(10, canvas.width // 60))
        for x0, y0, x1, y1, ins in box_items:
            dr.rectangle((x0 * s, y0 * s, x1 * s, y1 * s), outline=(0, 230, 255, 255), width=max(1, round(s / 2)))
            dr.text((x0 * s + 3, y0 * s + 2), '/'.join(ins), fill=(255, 255, 255, 255), font=fnt)
    bw, bh = box                                   # fit inside the box, keeping the shape (phones and iPads)
    k = min(bw / canvas.width, bh / canvas.height)
    return canvas.convert('RGB').resize((max(1, round(canvas.width * k)), max(1, round(canvas.height * k))), Image.LANCZOS)

def font(size):
    for f in ('arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'Helvetica.ttc'):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    try: return ImageFont.load_default(size=size)
    except Exception: return ImageFont.load_default()
F, FB = font(15), font(18)

# ---------- build pages ----------
ROWH = round(LW * 0.66)
want_l, want_p = ORIENT in ('both', 'landscape'), ORIENT in ('both', 'portrait')
GAP, LABELH, HEADH = 10, 22, 30
def tiles_for(lay, col):
    d = by[lay].get(col); out = []
    if d is None: return [None, None]
    try:
        if want_l: out.append(render(d, 'landscape', (LW, ROWH)))
        if want_p: out.append(render(d, 'portrait', (PW, ROWH)))
    except Exception as e:
        print('Could not draw', lay, col, '->', e); return [None]
    return out
os.makedirs(OUT, exist_ok=True)
pages = [layouts[i:i + ROWS] for i in range(0, len(layouts), ROWS)]
PW = round(ROWH * 0.75)                            # portrait box: wide enough for an iPad (3:4); phones just have spare room
pw = (LW if want_l else 0) + (PW if want_p else 0) + GAP
total_w = len(chosen) * (pw + GAP) + GAP
if COMPACT:
    COLW = lambda ts: sum(t.width + GAP for t in ts if t is not None)
    for pn, group in enumerate(pages, 1):
        rows = []                                           # per layout: [(colour, tiles)] for the colourways that exist
        for lay in group:
            row = []
            for col in chosen:
                if by[lay].get(col) is None: continue
                ts = [t for t in tiles_for(lay, col) if t is not None]
                if ts: row.append((col, ts))
            rows.append(row)
        W = max([GAP + sum(max(COLW(ts), 80) + GAP for _, ts in r) for r in rows] + [700])
        H = GAP + len(group) * (LABELH + 18 + ROWH + GAP * 2)
        page = Image.new('RGB', (W, H), (30, 30, 34)); dr = ImageDraw.Draw(page); y = GAP
        for lay, row in zip(group, rows):
            dr.text((GAP, y), lay, fill=(235, 235, 235), font=FB); y += LABELH + 2
            x = GAP
            for col, ts in row:
                dr.text((x, y), '' if col == '?' else col, fill=(255, 210, 90), font=F); xx = x
                for t in ts: page.paste(t, (xx, y + 18)); xx += t.width + GAP
                x += max(COLW(ts), 80) + GAP
            y += 18 + ROWH + GAP * 2 - 2
        fn = os.path.join(OUT, f'sheet_{pn:02d}.png'); page.save(fn); print('wrote', fn, f'({len(group)} layouts)')
    print(f'{len(layouts)} layouts, compact view ({len(chosen)} colourways allowed). Open the pictures.'); sys.exit(0)
for pn, group in enumerate(pages, 1):
    H = HEADH + len(group) * (ROWH + LABELH + GAP) + GAP
    page = Image.new('RGB', (max(total_w, 700), H), (30, 30, 34)); dr = ImageDraw.Draw(page)
    for ci, col in enumerate(chosen): dr.text((GAP + ci * (pw + GAP), 6), col, fill=(255, 210, 90), font=FB)
    y = HEADH
    for lay in group:
        dr.text((GAP, y), lay, fill=(235, 235, 235), font=F)
        for ci, col in enumerate(chosen):
            x = GAP + ci * (pw + GAP); ts = tiles_for(lay, col)
            if ts == [None, None] or ts == [None]:
                dr.text((x, y + LABELH + 20), 'missing' if by[lay].get(col) is None else 'cannot draw', fill=(255, 90, 90), font=F); continue
            for t in ts:
                if t is None: continue
                page.paste(t, (x, y + LABELH)); x += t.width + GAP
        y += ROWH + LABELH + GAP
    fn = os.path.join(OUT, f'sheet_{pn:02d}.png'); page.save(fn); print('wrote', fn, f'({len(group)} layouts)')
print(f'{len(layouts)} layouts x {len(chosen)} colourways ({", ".join(chosen)}). Open the pictures and compare down each column.')
