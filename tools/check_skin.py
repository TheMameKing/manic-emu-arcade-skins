#!/usr/bin/env python3
"""check_skin.py: a basic sanity check for Manic EMU .manicskin and Delta .deltaskin files.

    python check_skin.py PATH [PATH ...] [--quiet]

PATH can be a .manicskin or .deltaskin file, a folder (searched recursively), or a .zip of skins (zips inside zips are fine).
Exit code 0 = no errors, 1 = at least one ERROR. Warnings never fail the run. It never changes your files.

ERRORS   (the skin will probably not load or work)
  - not a zip, no info.json, info.json is not valid JSON
  - missing name / identifier / gameTypeIdentifier / representations
  - a layout has no background image, no mappingSize or no items
  - a Manic layout has no screens
  - a file named in info.json (background, button art, thumbstick art) is missing from the skin
  - a control has no inputs, or a frame that is not four numbers
  - two skins in the same run share an identifier
WARNINGS (usually a mistake, but check by eye)
  - an input name this tool does not know (typo?)   [Manic skins only, see below]
  - a control or screen sticking out of the canvas by more than 5 points
  - a background image whose shape does not match mappingSize
  - an asset that is not a real PDF, or a file in the skin that nothing uses
  - a Delta layout with no screens
  - two skins in the same run share a name

DELTA (.deltaskin) SUPPORT IS BASIC
  Delta skins are checked for the same structural problems (valid zip and info.json, files present, frames sane, duplicate
  identifiers). Differences from Manic skins:
  - The background may be listed as large, medium, small or resizable (PNG or PDF). Every listed file must exist.
  - Button and stick artwork may be PNG or PDF.
  - Input names are NOT checked, because every Delta console has its own set (z, c, touch screen inputs, and so on).
  - The background shape check is skipped for PDF backgrounds.
  It has not been tested against a wide range of Delta skins, so treat a clean result as "no structural problems found".

This is a generic checker. It does not know about any particular collection's naming, colour or button rules.
"""
import sys, os, io, json, zipfile, collections

EXTS = ('.manicskin', '.deltaskin')
KNOWN = {'up', 'down', 'left', 'right', 'a', 'b', 'x', 'y', 'l1', 'l2', 'r1', 'r2', 'start', 'select', 'menu',
         'quickLoad', 'quickSave', 'toggleFastForward',
         'leftThumbstickUp', 'leftThumbstickDown', 'leftThumbstickLeft', 'leftThumbstickRight',
         'rightThumbstickUp', 'rightThumbstickDown', 'rightThumbstickLeft', 'rightThumbstickRight'}
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
    return ([bg] if bg else []), bg, (None if bg else 'no background image (assets.large)')


def check(data, delta=False):
    errs, warns = [], []
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except Exception:
        return None, ['not a zip file'], []
    names = set(z.namelist())
    if 'info.json' not in names:
        return None, ['no info.json'], []
    try:
        info = json.loads(z.read('info.json'))
    except Exception as e:
        return None, ['info.json is not valid JSON: %s' % e], []
    for k in ('name', 'identifier', 'gameTypeIdentifier', 'representations'):
        if k not in info:
            errs.append('info.json has no "%s"' % k)
    used = {'info.json'}
    reps = info.get('representations') or {}
    for dev, modes in reps.items():
        for mode, orients in (modes or {}).items():
            for orient, rep in (orients or {}).items():
                if not isinstance(rep, dict):
                    continue
                where = '%s/%s/%s' % (dev, mode, orient)
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
                if not rep.get('screens'):
                    (warns if delta else errs).append(where + ': no screens')
                for s in rep.get('screens') or []:
                    f = s.get('outputFrame') or {}
                    if W and H and f and not inside(f, W, H):
                        warns.append(where + ': game screen sticks out of the canvas')
                items = rep.get('items')
                if not items:
                    errs.append(where + ': no items'); continue
                for i, it in enumerate(items):
                    tag = '%s item %d' % (where, i)
                    f = it.get('frame') or {}
                    if not all(isinstance(f.get(k), (int, float)) for k in ('x', 'y', 'width', 'height')):
                        errs.append(tag + ': frame is not x/y/width/height numbers')
                    elif W and H and not inside(f, W, H):
                        warns.append(tag + ': control sticks out of the canvas')
                    inp = it.get('inputs')
                    vals = list(inp.values()) if isinstance(inp, dict) else inp
                    if not vals:
                        errs.append(tag + ': no inputs')
                    if not delta:   # every Delta console has its own input names, so they are not checked
                        for v in vals or []:
                            if v not in KNOWN:
                                warns.append(tag + ': unknown input "%s"' % v)
                    art = (it.get('asset') or {}).get('normal')
                    if 'thumbstick' in it:
                        art = it['thumbstick'].get('name')
                    if art:
                        if art not in names:
                            errs.append(tag + ': %s is missing' % art)
                        else:
                            used.add(art)
                            if art.lower().endswith('.pdf') and not z.read(art)[:5] == b'%PDF-':
                                warns.append(tag + ': %s is not a real PDF' % art)
    for n in sorted(names - used):
        if not n.endswith('/') and '__MACOSX' not in n:
            warns.append('unused file in skin: ' + n)
    return info, errs, sorted(set(warns))


def inside(f, W, H):
    try:
        return (f['x'] >= -SLACK and f['y'] >= -SLACK and
                f['x'] + f['width'] <= W + SLACK and f['y'] + f['height'] <= H + SLACK)
    except Exception:
        return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    quiet = '--quiet' in sys.argv
    if not args or '-h' in sys.argv or '--help' in sys.argv:
        print(__doc__); sys.exit(0 if '-h' in sys.argv or '--help' in sys.argv else 1)
    n = bad = 0
    ids, names = collections.defaultdict(list), collections.defaultdict(list)
    nwarn = ndelta = 0
    for label, data in collect(args):
        n += 1
        delta = label.lower().endswith('.deltaskin')
        ndelta += delta
        info, errs, warns = check(data, delta)
        if info:
            ids[info.get('identifier')].append(label); names[info.get('name')].append(label)
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
            dup_err += 1; print('ERROR  identifier "%s" is used by %d skins' % (i, len(labs)))
    for nm, labs in names.items():
        if nm and len(labs) > 1 and not quiet:
            nwarn += 1; print('warning name "%s" is used by %d skins' % (nm, len(labs)))
    if not n:
        sys.exit('No .manicskin or .deltaskin files found.')
    print('\nchecked %d skins: %d with errors, %d warnings, %d duplicate identifiers' % (n, bad, nwarn, dup_err))
    if ndelta:
        print('note: %d .deltaskin file(s) got the basic Delta check (input names are not checked).' % ndelta)
    sys.exit(1 if bad or dup_err else 0)


if __name__ == '__main__':
    main()
