# Skin tools

Two small helper scripts for people making Manic EMU controller skins. They only read your skins and never change them.

| File | What it does |
|---|---|
| `check_skin.py` | Sanity check: valid zip, `info.json`, every referenced file present, inputs, canvas bounds, duplicate identifiers. |
| `contact_sheet.py` | Draws skins into pictures so you can compare layouts and colours by eye (phones and iPads). |
| `FORMAT_NOTES.md` | Notes on the skin format and the button numbering. |
| `contact_sheet_easy.py` | Same as contact_sheet.py, but simplified to run all colours every time unless specified otherwise. |

Both need Python 3 and Pillow (`pip install pillow`). `contact_sheet.py` draws the real button artwork if you also install PyMuPDF (`pip install pymupdf`); without it the artwork is drawn as outlines.

**Also if you try and run these on folders with spaces and  `manicskins` with spaces in the name it will fail to find the skin, they look for folder names as 1 word and its case sensitive. So if you try and run  `python contact_sheet_easy.py Purple skin folder --colours all` it will fail because of the space in the folder name or the `manicskins`. It needs to read like this or similar `Python contact_sheet_easy.py Purple_skin_folder --colours all ` and the folder it's self needs to be named like that, it can be any name you like but it needs -_. something besides spaces.**

It can also run `.deltaskins`, All you have to do is change the extension of the `.deltaskin` to `.manicskin` and run the contact sheet with the manic extension like above. then change the extension back to `deltaskin` since `manicskin` is a extension of deltas.

```
python check_skin.py my_skins_folder
python contact_sheet.py my_skins_folder --colours "Blackout,Soft Light"
python contact_sheet_easy.py .
```

Run either with `--help` for all options. For a mixed folder (different layouts and colours), add `--compact` to `contact_sheet.py` to leave out empty slots. 

Another tip if you want a higher resolution use the --width setting the higher the number the higher the resolution. examples below.

`python contact_sheet.py skin_folder --colours all --width 900 --rows 2` (this will give you a higher resolution than say `--width 300`) 

`python contact_sheet.py skin_folder --colours "your color (in the json)" --compact` (use `--compact` if you have a variety of skins with different button counts and down want to see empty slots if you are looking at like a variety pack set of skins

`python contact_sheet.py skin_folder --colours all  --rows 200` (you can change the amount of rows there are in each sheet, so if you want to scan a large collection you can scan 200 on one sheet, idk the limit but i've done 224 on a sheet. Expect it to take a little bit with a giant collection. single and small sheets are near instant.

You can also open either of the scripts in notepad or similar app to see these options and more, and the list of errors and warnings for `check_skin.py` are in its script, these are here to make it easier to use. 

These tools are generic. They do not know the naming, colour or button-count rules of any particular collection.

## Preview
Running `contact_sheet.py` over a folder of skins writes numbered pictures to `contact_sheets/`:

![contact_sheet.py output in a terminal](images/Showcase_cmd.png)

![sample sheet](images/showcase_compact.png)

![more examples](images/contact_sheet_cmd.png)

![another contact sheet](images/blackout_softlight_contact_sheet.png)

<details>
<summary><b>More Sheet Examples </b></summary>

<br> 

**Sheet 1**

<img src="images/sheet_01.png" width="1000" alt="sheet above split into 6 sheets for better view">

**Sheet 2**

<img src="images/sheet_02.png" width="1000" alt="sheet 2">

**Sheet 3**

<img src="images/sheet_03.png" width="1000" alt="sheet 3">

**Sheet 4**

<img src="images/sheet_04.png" width="1000" alt="Sheet 4">

**Sheet 5**

<img src="images/sheet_05.png" width="1000" alt="Sheet 5">

**Sheet 6**

<img src="images/sheet_06.png" width="1000" alt="Sheet 6">

</details>
Released under the MIT License, provided as-is with no warranty. The skins themselves are CC BY 4.0.
