# Release Checklist

Zips are too big for normal repo files, so the repo holds only the docs, and the 32 zips go on a **Release**.
It is easier on a computer, but it works from an iPhone in Safari too (tip: tap the "aA" button in the address bar and choose **Request Desktop Website** if a GitHub page looks cut down).

## 0. Test first

- [ ] Try one Normal and one Full Screen skin from each layout on your device
- [ ] 4 Button Tekken-Rival Fix: check a fighter (Tekken, Rival Schools)
- [ ] Twin Stick: check Smash TV or Total Carnage
- [ ] If something is wrong, fix it **before** uploading, so you only upload once

## 1. Make the repo

- [ ] On github.com, tap **+** then **New repository**
- [ ] Name it something like `manic-emu-arcade-skins`, set it to **Public**
- [ ] Leave "Add a README" **unticked** (this folder already has one)
- [ ] Create the repository

## 2. Upload the docs

- [ ] Unzip this starter folder
- [ ] In the new repo: **Add file > Upload files**, then choose `README.md`, `LICENSE` and `RELEASE_CHECKLIST.md` and the two preview images (`arcade-skins-colorways.png` and `arcade-skins-layouts.png`)
- [ ] Commit the changes
- [ ] `LICENSE` already says TheMameKing and CC BY 4.0. If you'd rather use a different license, change it and update the last line of the README

## 3. Create the release

- [ ] Repo page > **Releases** > **Create a new release**
- [ ] Tag: `v1.0` (choose "Create new tag")
- [ ] Title: `Arcade Skins v1.0`
- [ ] Description: paste in everything from `RELEASE_NOTES.md`
- [ ] Attach all 32 zips from the list below (drag and drop on a computer; on iPhone use the file picker and pick several at once). Wait for every one to finish uploading.
- [ ] **Publish release**

Note: GitHub turns spaces in file names into dots (for example `4.Button.Classic.Zip.-.Part.1.zip`). That is normal. If you'd rather keep it tidy, rename the zips with dashes before uploading.

## 4. The 32 zips

Tick each one off as you attach it.

**1 Button**
- [ ] 1 Button Zip - Part 1
- [ ] 1 Button Zip - Part 2
- [ ] 1 Button Full Screen Zip - Part 1
- [ ] 1 Button Full Screen Zip - Part 2

**2 Button**
- [ ] 2 Button Zip - Part 1
- [ ] 2 Button Zip - Part 2
- [ ] 2 Button Full Screen Zip - Part 1
- [ ] 2 Button Full Screen Zip - Part 2

**3 Button**
- [ ] 3 Button Zip - Part 1
- [ ] 3 Button Zip - Part 2
- [ ] 3 Button Full Screen Zip - Part 1
- [ ] 3 Button Full Screen Zip - Part 2

**4 Button Classic**
- [ ] 4 Button Classic Zip - Part 1
- [ ] 4 Button Classic Zip - Part 2
- [ ] 4 Button Classic Full Screen Zip - Part 1
- [ ] 4 Button Classic Full Screen Zip - Part 2

**4 Button Tekken-Rival Fix**
- [ ] 4 Button Tekken-Rival Fix Zip - Part 1
- [ ] 4 Button Tekken-Rival Fix Zip - Part 2
- [ ] 4 Button Tekken-Rival Fix Full Screen Zip - Part 1
- [ ] 4 Button Tekken-Rival Fix Full Screen Zip - Part 2

**5 Button**
- [ ] 5 Button Zip - Part 1
- [ ] 5 Button Zip - Part 2
- [ ] 5 Button Full Screen Zip - Part 1
- [ ] 5 Button Full Screen Zip - Part 2

**6 Button**
- [ ] 6 Button Zip - Part 1
- [ ] 6 Button Zip - Part 2
- [ ] 6 Button Full Screen Zip - Part 1
- [ ] 6 Button Full Screen Zip - Part 2

**Twin Stick**
- [ ] Twin Stick Zip - Part 1
- [ ] Twin Stick Zip - Part 2
- [ ] Twin Stick Full Screen Zip - Part 1
- [ ] Twin Stick Full Screen Zip - Part 2

### Do NOT upload

- Any plain "4 Button Zip" or "4 Button Full Screen Zip" with no "Classic" or "Tekken" in the name (old copies of the fix)
- Any "Arcade 6 Pro - Favorites" zip (replaced by `6 Button Zip`)
- Max Screen or 8-button zips (dropped from this release)

## 5. After publishing

- [ ] Open the release page and count **32** zip files
- [ ] Download one zip from the live page, unzip it, import a skin, confirm it loads
- [ ] Check the README link to Releases works
