## macroR6 – Click Move Down (Standalone-App)

Kleine Windows-App mit UI-Regler:

- **Regler**: Pixel, die der Mauszeiger nach unten wandert
- **Wenn aktiv**: bei **Linksklick** wird die Maus um den Reglerwert nach unten bewegt
- **Toggle**: global mit der Taste **`#`** (zusätzlich **`F8`** als Fallback)

### Setup (Entwicklung)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### Build zur `.exe` (Standalone)

```powershell
.\.venv\Scripts\Activate.ps1
pyinstaller --onefile --noconsole --name "ClickMoveDown" app.py
```

Die fertige EXE liegt dann unter `dist\ClickMoveDown.exe`.

### Hinweise

- Wenn `#` auf deinem Layout nicht zuverlässig erkannt wird, nutze **F8** (ist absichtlich eingebaut).
- Manche Spiele/Anti-Cheat-Umgebungen können das Steuern von Maus/Hotkeys blockieren.
