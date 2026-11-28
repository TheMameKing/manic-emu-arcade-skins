#!/usr/bin/env python3
"""check_skin.py: a basic sanity check for Manic EMU .manicskin and Delta .deltaskin files.

    python check_skin.py PATH [PATH ...] [--quiet] [--debug]

PATH can be a .manicskin or .deltaskin file, a folder (searched recursively), or a .zip of skins (zips inside zips are fine).
Exit code 0 = no errors, 1 = at least one ERROR. Warnings never fail the run. It never changes your files.

ERRORS   (the skin will probably not load or work)
  - not a zip, no info.json, info.json is not valid JSON
  - missing name / identifier / gameTypeIdentifier / representations
  - a layout has no background image, no mappingSize or no items
  - a Manic layout has no screens (the older gameScreenFrame key is accepted, with a warning)
  - a file named in info.json (background, button art, thumbstick art) is missing from the skin
  - a control has no inputs, or a frame that is not four numbers
  - two skins in the same run share an identifier
WARNINGS (usually a mistake, but check by eye)
  - an input name this tool does not know (typo?)   [Manic and Delta; the list is shared, not per console]
  - a control or screen sticking out of the canvas by more than 5 points
  - a background image whose shape does not match mappingSize
  - an iPhone edgeToEdge layout whose mappingSize is 16:9 (home-button phone), which leaves a black bar on notch phones
  - an asset that is not a real PDF, or a file in the skin that nothing uses
  - a Delta layout with no screens or gameScreenFrame
  - (tv entries, which have items/screens directly under "tv", get an input check only)
  - a layout type other than standard, edgeToEdge or splitView (e.g. cover, inner): warned, and an empty one is not an error
  - a misspelt layout or item key (e.g. extendedEdge), which the app would ignore
  - two skins in the same run share a name

DELTA (.deltaskin) SUPPORT IS BASIC
  Delta skins are checked for the same structural problems (valid zip and info.json, files present, frames sane, duplicate
  identifiers). Differences from Manic skins:
  - The background may be listed as large, medium, small or resizable (PNG or PDF). Every listed file must exist.
  - Button and stick artwork may be PNG or PDF.
  - Input names are compared with the same shared list as Manic skins (it includes z, c, mode, cUp.., touchScreenX/Y), but NOT per console,
    so an input that is valid on some other system will pass.
  - The background shape check is skipped for PDF backgrounds.
  It has not been tested against a wide range of Delta skins, so treat a clean result as "no structural problems found".

This is a generic checker. It does not know about any particular collection's naming, colour or button rules.
"""
import sys, os, io, json, zipfile, collections, hashlib, difflib

EXTS = ('.manicskin', '.deltaskin')
KNOWN = {
    'up', 'down', 'left', 'right',                                         # D-pad directions
    'a', 'b', 'c', 'x', 'y',                                               # face buttons
    'l', 'r', 'l1', 'l2', 'r1', 'r2', 'z',                                 # shoulders / specials
    'start', 'select', 'mode',                                             # system buttons
    'cUp', 'cDown', 'cLeft', 'cRight',                                     # N64 C-buttons
    'analogStickUp', 'analogStickDown', 'analogStickLeft', 'analogStickRight',   # Delta's analog names
    'leftThumbstickUp', 'leftThumbstickDown', 'leftThumbstickLeft', 'leftThumbstickRight',   # Manic's analog names
    'rightThumbstickUp', 'rightThumbstickDown', 'rightThumbstickLeft', 'rightThumbstickRight',
    'touchScreenX', 'touchScreenY',                                        # DS / 3DS touch screen
    'menu', 'quickSave', 'quickLoad', 'fastForward', 'toggleFastForward',  # Delta / Manic feature buttons
    'volume', 'reverseScreens', 'toggleAnalog', 'retroAchievements',      # seen in working third-party skins
    'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'num7', 'num8', 'num9', 'star', 'pound',   # keypad (seen in an Atari Jaguar skin)
    'rightDpadUp', 'rightDpadDown', 'rightDpadLeft', 'rightDpadRight',    # second D-pad (seen in a Virtual Boy skin)
}
LAYOUT_KEYS = {'assets', 'mappingSize', 'screens', 'gameScreenFrame', 'items', 'extendedEdges', 'translucent', 'menuInsets', 'placement'}
ITEM_KEYS = {'inputs', 'frame', 'extendedEdges', 'asset', 'thumbstick'}
KNOWN_MODES = {'standard', 'edgeToEdge', 'splitView'}   # layout types the apps are known to use
SLACK = 5   # points a control may stick out of the canvas before we warn
BG_ORDER = ('large', 'medium', 'small', 'resizable')   # Delta skins can list any of these; Manic skins use "large"


def collect(paths):
    """yield (label, bytes) for every .manicskin / .deltaskin found."""
    def from_zip(label, data):
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
        except Exception:
            return
        for n in z.namelist():
            if n.endswith('/') or '__MACOSX' in n:
                continue
            if n.lower().endswith(EXTS):
                yield label + ' > ' + os.path.basename(n), z.read(n)
            elif n.lower().endswith('.zip'):
                yield from from_zip(label + ' > ' + n, z.read(n))
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in sorted(files):
                    fp = os.path.join(root, f)
                    if f.lower().endswith(EXTS):
                        yield fp, open(fp, 'rb').read()
                    elif f.lower().endswith('.zip'):
                        yield from from_zip(fp, open(fp, 'rb').read())
        elif p.lower().endswith('.zip'):
            yield from from_zip(p, open(p, 'rb').read())
        elif os.path.isfile(p):
            yield p, open(p, 'rb').read()
        else:
            print('not found:', p)


def backgrounds(assets, delta):
    """Return (files to verify, file to use for the shape check, error text or None)."""
    low = {str(k).lower(): v for k, v in (assets or {}).items() if isinstance(v, str)}
    if delta:
        files = list(low.values())
        main = next((low[k] for k in BG_ORDER if k in low), None)
        return files, main, (None if files else 'no background image (assets)')
    bg = low.get('large')
    if not bg:                                   # some working Manic skins list only a 'resizable' PDF
        alt = next((low[k] for k in BG_ORDER if k in low), None)
        if alt:
            return [alt], alt, None
    return ([bg] if bg else []), bg, (None if bg else 'no background image (assets.large)')


def check(data, delta=False):
    errs, warns = [], []
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except Exception:
        return None, ['not a zip file'], [], []
    names = set(z.namelist())
    if 'info.json' not in names:
        return None, ['no info.json'], [], []
    try:
        info = json.loads(z.read('info.json'))
    except Exception as e:
        return None, ['info.json is not valid JSON: %s' % e], [], []
    for k in ('name', 'identifier', 'gameTypeIdentifier', 'representations'):
        if k not in info:
            errs.append('info.json has no "%s"' % k)
    used = {'info.json'}
    reps = info.get('representations') or {}
    if not isinstance(reps, dict):
        errs.append('"representations" is not a dictionary of devices'); reps = {}
    for dev, modes in reps.items():
        if dev == 'tv' and isinstance(modes, dict) and ('items' in modes or 'screens' in modes):
            # Apple TV skins have no portrait/landscape layouts: items and screens sit directly under "tv", with 0-1 fractions
            for i, it in enumerate(modes.get('items') or []):
                inp = it.get('inputs') if isinstance(it, dict) else None
                vals = list(inp.values()) if isinstance(inp, dict) else inp
                if not vals:
                    errs.append('tv item %d: no inputs' % i)
                for v in vals or []:
                    if v not in KNOWN:
                        warns.append('tv item %d: unknown input "%s" (typo? fine if it is valid for this system)' % (i, v))
            continue
        if not isinstance(modes, dict):
            warns.append('%s: not a dictionary of layouts, skipped' % dev)
            continue
        for mode, orients in modes.items():
            if not isinstance(orients, dict):      # e.g. a list; not a layout this tool understands
                warns.append('%s/%s: is a %s, not portrait/landscape layouts, skipped' % (dev, mode, type(orients).__name__))
                continue
            for orient, rep in orients.items():
                if not isinstance(rep, dict):
                    warns.append('%s/%s/%s: is a %s, not a layout, skipped' % (dev, mode, orient, type(rep).__name__))
                    continue
                where = '%s/%s/%s' % (dev, mode, orient)
                odd_mode = mode not in KNOWN_MODES
                if odd_mode:
                    warns.append(where + ': "%s" is not a layout type the app is known to use (standard, edgeToEdge, splitView); the app may ignore it' % mode)
                files, bg, bg_err = backgrounds(rep.get('assets'), delta)
                if bg_err:
                    errs.append(where + ': ' + bg_err)
                for f in files:
                    if f not in names:
                        errs.append(where + ': background %s is missing' % f)
                    else:
                        used.add(f)
                ms = rep.get('mappingSize') or {}
                W, H = ms.get('width'), ms.get('height')
                if not (W and H):
                    errs.append(where + ': no mappingSize'); W = H = None
                if bg in names and W and H and not bg.lower().endswith('.pdf'):
                    try:
                        from PIL import Image
                        iw, ih = Image.open(io.BytesIO(z.read(bg))).size
                        if abs(iw / ih - W / H) > 0.02:
                            warns.append(where + ': background is %dx%d but mappingSize is %sx%s (different shape)' % (iw, ih, W, H))
                    except ImportError:
                        pass
                    except Exception:
                        warns.append(where + ': background image could not be read')
                for k in rep:      # a misspelt key is silently ignored by the app, e.g. extendedEdge instead of extendedEdges
                    close = difflib.get_close_matches(k, LAYOUT_KEYS, n=1, cutoff=0.8) if k not in LAYOUT_KEYS else []
                    if close:
                        warns.append(where + ': layout key "%s" is not recognised (typo for "%s"?)' % (k, close[0]))
                if W and H and dev == 'iphone' and mode == 'edgeToEdge' and (rep.get('screens') or rep.get('gameScreenFrame')):
                    long_, short_ = max(W, H), min(W, H)          # notch iPhones are about 2.16:1; a 16:9 layout leaves a black bar
                    if long_ / short_ < 1.9:
                        warns.append(where + ': mappingSize %sx%s is a home-button-phone shape (16:9); on a notch iPhone this leaves a black bar. Edge-to-edge layouts normally use about 2.16:1 (e.g. 375x812)' % (W, H))
                if not rep.get('screens'):
                    if rep.get('gameScreenFrame'):         # older skins give the screen as gameScreenFrame
                        if not delta:
                            warns.append(where + ': uses the older "gameScreenFrame" key instead of "screens" (still loads in Manic)')
                    else:
                        (warns if delta else errs).append(where + ': no screens (and no gameScreenFrame)')
                for s in rep.get('screens') or []:
                    f = s.get('outputFrame') or {}
                    if not delta and W and H and f and not inside(f, W, H):   # Delta skins often oversize the screen on purpose
                        warns.append(where + ': game screen sticks out of the canvas')
                items = rep.get('items')
                if not items:
                    (warns if odd_mode else errs).append(where + ': no items'); continue
                for i, it in enumerate(items):
                    tag = '%s item %d' % (where, i)
                    for k in it:
                        close = difflib.get_close_matches(k, ITEM_KEYS, n=1, cutoff=0.8) if k not in ITEM_KEYS else []
                        if close:
                            warns.append(tag + ': item key "%s" is not recognised (typo for "%s"?)' % (k, close[0]))
                    f = it.get('frame') or {}
                    if not all(isinstance(f.get(k), (int, float)) for k in ('x', 'y', 'width', 'height')):
                        errs.append(tag + ': frame is not x/y/width/height numbers')
                    elif W and H and not inside(f, W, H):
                        warns.append(tag + ': control sticks out of the canvas')
                    inp = it.get('inputs')
                    vals = list(inp.values()) if isinstance(inp, dict) else inp
                    if not vals:
                        errs.append(tag + ': no inputs')
                    for v in vals or []:      # one shared list for Manic and Delta; only a WARNING, because other systems may use more names
                        if v not in KNOWN:
                            warns.append(tag + ': unknown input "%s" (typo? fine if it is valid for this system)' % v)
                    arts = [v for v in (it.get('asset') or {}).values() if isinstance(v, str)]   # normal, and any other state such as pressed
                    if 'thumbstick' in it:
                        arts.append(it['thumbstick'].get('name'))
                    for art in arts:
                        if not art:
                            continue
                        if art not in names:
                            errs.append(tag + ': %s is missing' % art)
                        else:
                            used.add(art)
                            if art.lower().endswith('.pdf') and not z.read(art)[:5] == b'%PDF-':
                                warns.append(tag + ': %s is not a real PDF' % art)
    unused = [n for n in sorted(names - used) if not n.endswith('/') and '__MACOSX' not in n]
    warns += ['unused file in skin: ' + n for n in unused]
    return info, errs, sorted(set(warns)), unused


def inside(f, W, H):
    try:
        return (f['x'] >= -SLACK and f['y'] >= -SLACK and
                f['x'] + f['width'] <= W + SLACK and f['y'] + f['height'] <= H + SLACK)
    except Exception:
        return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]   # options: --quiet, --debug
    quiet = '--quiet' in sys.argv
    if not args or '-h' in sys.argv or '--help' in sys.argv:
        print(__doc__); sys.exit(0 if '-h' in sys.argv or '--help' in sys.argv else 1)
    n = bad = 0
    ids, names = collections.defaultdict(list), collections.defaultdict(list)
    nwarn = ndelta = same = 0
    for label, data in collect(args):
        n += 1
        delta = label.lower().endswith('.deltaskin')
        ndelta += delta
        try:
            info, errs, warns, unused = check(data, delta)
        except Exception as e:      # one odd skin must never stop the whole run
            info, warns, unused = None, [], []
            errs = ['the checker could not finish this skin (%s: %s). It may still work in the app; please report it' % (type(e).__name__, e)]
            if '--debug' in sys.argv:
                import traceback; traceback.print_exc()
        if info:
            ids[info.get('identifier')].append((label, hashlib.sha1(data).hexdigest())); names[info.get('name')].append(label)
        nwarn += len(warns)
        if errs:
            bad += 1
        if errs or (warns and not quiet):
            print(label)
            for e in errs:
                print('   ERROR  ', e)
            for w in warns:
                print('   warning', w)
    dup_err = 0
    for i, labs in ids.items():
        if i and len(labs) > 1:
            if len({h for _, h in labs}) == 1:     # byte-identical copies (the same skin in several packs) are not a clash
                same += 1; continue
            dup_err += 1; print('ERROR  identifier "%s" is used by %d different skins' % (i, len(labs)))
    for nm, labs in names.items():
        if nm and len(labs) > 1 and not quiet:
            nwarn += 1; print('warning name "%s" is used by %d skins' % (nm, len(labs)))
    if not n:
        sys.exit('No .manicskin or .deltaskin files found.')
    print('\nchecked %d skins: %d with errors, %d warnings, %d duplicate identifiers' % (n, bad, nwarn, dup_err))
    if same:
        print('note: %d identifier(s) appear in more than one pack, but the skins are identical copies (not counted as duplicates).' % same)
    if ndelta:
        print('note: %d .deltaskin file(s) got the basic Delta check (input names are compared with the shared list, not per console).' % ndelta)
    sys.exit(1 if bad or dup_err else 0)


if __name__ == '__main__':
    main()
