**CIE A-Level Past Paper Question Extractor & Organizer**

Automatically downloads CIE A-Level past papers, extracts individual questions, and provides a UI for organizing them by topic.

## Features

**Parallel Processing Pipeline**
- **Downloader**: Automatically fetches PDFs from bestexamhelp.com using Selenium
- **Slicer**: Extracts individual questions from PDFs as images
- **Sorter**: Clean UI for manually tagging questions by topic

**Smart Organization**
- Each question saved as a separate image
- Automatic matching of questions with mark schemes
- Topic-based folder structure
- JSON database tracking all metadata

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Chrome/Chromium browser** (for Selenium)
3. **ChromeDriver** (matching your Chrome version)

### Install ChromeDriver

```bash
# Ubuntu/Debian/Linux Mint
sudo apt update
sudo apt install chromium-chromedriver

# Or download manually from:
# https://chromedriver.chromium.org/downloads
```

### Install Python Dependencies

```bash
pip install -r requirements.txt --break-system-packages
```

Required packages:
- `selenium` - Web scraping
- `Pillow` - Image processing
- `PyMuPDF` - PDF parsing
- `pdf2image` - PDF to image conversion
- `watchdog` - File system monitoring

## Usage

### Quick Start - Run Everything

```bash
python3 main.py
```

Select option **1** to run all workers together.

### Run Modes

**Mode 1: Full Pipeline** (Recommended for first run)
```bash
python3 main.py
# Select: 1
```
Runs Downloader -> Slicer -> Sorter in parallel

**Mode 2: Download Only**
```bash
python3 main.py
# Select: 2
```
Just downloads PDFs (useful for batch downloading overnight)

**Mode 3: Slice Only**
```bash
python3 main.py
# Select: 3
```
Processes existing PDFs to extract questions

**Mode 4: Sort Only**
```bash
python3 main.py
# Select: 4
```
Opens UI to tag already-extracted questions

**Mode 5: Slice + Sort** (Recommended if you have PDFs)
```bash
python3 main.py
# Select: 5
```
Process PDFs and tag questions (skips downloading)

### How the Pipeline Works

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ DOWNLOADER  │────────▶│   SLICER    │────────▶│   SORTER    │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │                       │
      ▼                       ▼                       ▼
  data/pdfs/         data/raw_questions/    data/sorted_questions/
```

Each worker runs independently:
- **Downloader** saves PDFs to `data/pdfs/`
- **Slicer** watches `pdfs/` and extracts questions to `raw_questions/`
- **Sorter** displays questions from `raw_questions/` for tagging

## Sorter UI Guide

### Keyboard Shortcuts
- **1-9**: Quick assign to topic (based on current subject's topic list)
- **→** or **Space**: Skip question
- **←**: Go back to previous question

### Workflow
1. Question displays with metadata (subject, session, paper, question number)
2. Select the subject using radio buttons (if needed)
3. Click a topic button or press number key
4. Question auto-saves and moves to next

### Progress Tracking
- Progress bar shows completion percentage
- All tagged questions automatically saved to database
- Images copied to topic-specific folders

## Configuration

Edit `config.py` to customize:

```python
# Year range for downloads
START_YEAR = 2015
END_YEAR = 2024

# Browser mode
HEADLESS_MODE = False  # Set True for background operation

# Add more topics per subject
SUBJECTS["9702"]["topics"].append("Your Custom Topic")
```

## Database Format

All metadata stored in `data/questions_db.json`:

```json
{
  "9702_s24_qp_42.pdf": {
    "processed": true,
    "questions": [
      {
        "id": "9702_s24_qp_42_1",
        "subject_code": "9702",
        "session": "s24",
        "paper_num": "42",
        "question_num": "1",
        "page_num": 1,
        "image_path": "data/raw_questions/9702_s24_qp_42_1.png",
        "topic": "Mechanics",
        "marks": null
      }
    ],
    "total_questions": 12
  }
}
```

## License & Legal

This tool is for **personal educational use only**.

- Respects bestexamhelp.com's terms of use
- Does not redistribute copyrighted content
- Uses publicly available past papers

## Contributing

Found a bug? Have a feature request? Want to add support for more subjects?

Open an issue or submit a pull request!

## Credits

Built with:
- Selenium (web automation)
- PyMuPDF (PDF processing)
- Tkinter (GUI)
- Watchdog (file monitoring)

---

**Happy studying!**

Made with love for CIE students worldwide
> *please star the project ts took way too long*