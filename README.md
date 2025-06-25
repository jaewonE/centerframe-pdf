# CenterFrame PDF

[ [English](README.md) | [한국어](README.ko.md) ]

**Center certificate-style PDFs easily via drag & drop or command line.**

---

## Table of Contents

1. [Features](#features)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Building Stand-alone Binaries](#building-stand-alone-binaries)
6. [Contributing](#contributing)
7. [License](#license)

---

## Features

- **Automatic centering** – `center_pdf` analyses each page and translates content so it is horizontally **and** vertically centered while avoiding clipping.
- **CLI utility** – batch convert all PDFs inside a `pdfs` folder using `center_pdf.py`.
- **Drag & drop GUI** – friendly PyQt6 application (`pdf_transfer_app.py`) for Windows and macOS.
- **Progress reporting and cancellation** – GUI shows a progress bar and allows cancelling ongoing jobs.
- **Persistent settings** – the chosen output directory is stored via Qt `QSettings`.

---

## Quick Start

```bash
# 1. Install dependencies
uv venv --python=3.11
uv sync

# 2. Launch the GUI
uv run pdf_transfer_app.py
```

---

## Installation

Install Python 3.11 or later and ensure `pip` is available. Required Python packages are listed in `pyproject.toml`:

```
pdfplumber
pypdf2
pyqt6
```

You can install them manually or run `uv sync`.

---

## Usage

### Command Line

Run `center_pdf.py` to process every PDF found in the `pdfs` directory. New files are written with the `centered_` prefix.

```bash
uv run center_pdf.py
```

### GUI Application

1. Start the app with `python pdf_transfer_app.py`.
2. Choose an output directory.
3. Drag one or more PDF files into the list (or use **Add Files...**).
4. Click **Start Conversion**. Progress is shown for each file.

---

## Building Stand-alone Binaries

PyInstaller can generate self-contained executables.

```bash
pyinstaller --onefile --windowed pdf_transfer_app.py
```

The resulting binary runs without a separate Python install.

## Building Stand-alone Binaries

The project works out-of-the-box with **PyInstaller**.

<details>
<summary><strong>Windows (x64)</strong></summary>

```cmd
pyinstaller ^
  --noconsole --onefile ^
  --name "Centerframe-PDF" ^
  --icon "assets\centerframe_pdf.ico" ^
  pdf_transfer_app.py
```

</details>

<details>
<summary><strong>macOS (Apple Silicon)</strong></summary>

```bash
pyinstaller \
  --onefile --windowed \
  --target-architecture arm64 \
  --name "Centerframe-PDF" \
  --icon "assets/centerframe_pdf.icns" \
  pdf_transfer_app.py
```

</details>

The generated executable is fully self-contained—no Python installation required for end-users.

---

## Contributing

1. Fork the repository and create your branch: `git checkout -b feature/my-change`.
2. Commit your changes with clear messages.
3. Push to the branch and open a pull request.

Please ensure code follows PEP 8 and includes sensible tests where possible.

---

## License

Released under the **GNU General Public License v3.0**. See [`LICENSE`](LICENSE) for details.
