## macroR6 – Click Move Down (Standalone-App)

Kleine Windows-App mit UI-Regler:

- **Regler**: Pixel, die der Mauszeiger nach unten wandert
- **Wenn aktiv**: bei **Linksklick** wird die Maus um den Reglerwert nach unten bewegt
- **Toggle**: global mit der Taste **`#`** (zusätzlich **`F8`** als Fallback)

### Python / pip installieren (falls nicht vorhanden)

`pip` kommt bei Windows normalerweise **mit Python** mit.

**Option A: per winget (empfohlen)**

```powershell
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
```

Danach ein **neues** PowerShell-Fenster öffnen und prüfen:

```powershell
python --version
python -m pip --version
```

**Option B: Installer von python.org**

- Python 3.11+ (64-bit) installieren
- Im Installer anhaken: **Add python.exe to PATH**

**Wenn `python` dich in den Microsoft Store umleitet**

Windows Alias deaktivieren:

- Settings → Apps → Advanced app settings → App execution aliases
- **python.exe** und **python3.exe** → **Off**

### Setup (Entwicklung)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### Build zur `.exe` (Standalone)

**Einfach (ohne Activate.ps1 / ohne Execution-Policy-Probleme):**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m PyInstaller --onefile --noconsole --name "ClickMoveDown" app.py
```

**Oder per Doppelklick:** `build_exe.bat`

```powershell
.\.venv\Scripts\Activate.ps1
pyinstaller --onefile --noconsole --name "ClickMoveDown" app.py
```

Die fertige EXE liegt dann unter `dist\ClickMoveDown.exe`.

### Hinweise

- Wenn `#` auf deinem Layout nicht zuverlässig erkannt wird, nutze **F8** (ist absichtlich eingebaut).
- Manche Spiele/Anti-Cheat-Umgebungen können das Steuern von Maus/Hotkeys blockieren.
