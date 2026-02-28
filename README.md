**CIE A-Level Past Paper Question Extractor & Organizer**

Automatically downloads CIE A-Level past papers, extracts individual questions, and provides a UI for organizing them by topic.

## Features

- **Automatically Download Past Papers**
- **Automatically Slice Questions into Images**
- **Manually sort the questions in the ~~ugly asf~~ beautiful UI**

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
Do this if ur on windows
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

Installs packages:
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
Downloads papers, slices them up, and asks you to sort them all in parallel.

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
Processes existing PDFs to extract questions (useful for sociopaths who don't like saving time by using option 1)

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

Each worker runs independently:
- **Downloader** saves PDFs to `data/pdfs/`
- **Slicer** watches `pdfs/` and extracts questions as images to `raw_questions/`
- **Sorter** displays questions from `raw_questions/` for tagging

## Sorter UI Guide

### Keyboard Shortcuts
- **1-9**: Quick assign to topic (based on current subject's topic list)
- **Left Arrow** or **Space**: Skip question
- **Right Arrow**: Go back to previous question

### Workflow
1. Question displays with metadata (subject, session, paper, question number)
2. Select the subject using radio buttons (if needed)
3. Click a topic button or press number key
4. Question auto-saves and moves to next

### Progress Tracking
- Progress percentage in the top right shows completion percentage
- All tagged questions automatically saved to database (it's js a json file lol)
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

[@Myst1cS04p](https://myst1cs04p.github.io/)

---

**Happy studying!**

Made with love for CIE students worldwide
> *please star the project ts took way too long*
