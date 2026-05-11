# inidiff

inidiff is a desktop tool for comparing and validating stringtable.ini translation files. It helps mod translators ensure their translations are complete and consistent. It was made for translating the videogame series Gothic, but is usable elsewhere too.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
## Features
- **Compare two files** – spot missing and extra keys between a translation (File A) and a reference (File B).
    - You may also use English content scanner for your translation at the same time.

- **English content scanner** – detect entries in a stringtable.ini that have placeholders or .

- **Folder comparison** – recursively compare entire mod folders, matching stringtable.ini files by their relative path inside Mods/.

- **Drag & drop support** – drop files or folders directly into the interface (requires tkinterdnd2).

- **Clear reports** – results displayed in‑app with line numbers, colour‑coded tags, and copyable text.

## Installation

### Clone the repository
```bash
git clone https://github.com/SolaraCZ/inidiff.git
cd inidiff
```
### Install dependencies
- Python **3.8 or newer** – [Download from python.org](https://www.python.org/downloads/)

The core tool only needs **Python 3.8+ with Tkinter** (usually included).
For drag & drop support, install the optional dependency: **tkinterdnd2**
```bash
pip install tkinterdnd2
```
Note: On some Linux distributions you may need to install **python3-tk** separately e.g. 
```bash
sudo apt install python3-tk
```
### Run the application
```bash
python inidiff.py
```
## Usage

The GUI is divided into three tabs:
### 1. Compare Files
Select a translation file (File A) and a reference file (File B).

Optionally enable “Run English‑check on translation (File A)”.

Click COMPARE FILES.
The report shows:

- Number of lines / keys in each file

- Keys missing from the translation (present in B, absent in A)

- Keys extra in the translation (present in A, absent in B)

- If enabled, a list of translation entries that fail the English check

### 2. Check for English

Choose a single stringtable.ini file.

Click SCAN FILE.
Every entry is analysed to determine whether it contains English letters.
Entries that fail the check (no English letters, or explicitly marked as non‑English) are listed with:  
- line numbers
- reason for failure

How the English Check Works:

The tool looks at the value part of each key = value line and considers it “passes the English check” if:
- It contains at least one alphabetic character (A–Z, a–z), and
- It does not start with
    - ;;
    - [en]
    - [eng]
- or the standalone tokens
    - en
    - eng

This heuristic catches entries where the translator forgot to replace placeholder English text, while ignoring comments, headers, and properly marked non‑English entries.

### 3. Folder Compare

Select two folders – typically a translation folder (Folder A) and a modpack (Folder B).

The tool scans both folders for stringtable.ini files and matches them by their path after the Mods/ directory (case‑insensitive).

For each matched pair it performs: 
- Compare Files check
- English scan
- summarises missing/extra keys and English fails.

## Dependencies

- python ≥ 3.8
- tkinter (standard library)
- tkinterdnd2 (optional – enables drag & drop)

## Contributing
Pull requests are welcome! Please open an issue first to discuss any major changes.

## License

[MIT](https://github.com/SolaraCZ/inidiff/blob/main/LICENSE)