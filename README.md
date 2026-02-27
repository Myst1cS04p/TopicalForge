# TopicalForge

**CIE A-Level Past Paper Question Extractor & Organizer**

Automatically downloads CIE A-Level past papers, extracts individual questions, and provides a UI for organizing them by topic.

## Features

🔄 **Parallel Processing Pipeline**
- **Downloader**: Automatically fetches PDFs from bestexamhelp.com using Selenium
- **Slicer**: Extracts individual questions from PDFs as images
- **Sorter**: Clean UI for manually tagging questions by topic

📚 **Supported Subjects**
- Physics (9702)
- Mathematics (9709)
- Computer Science (9618)

🎯 **Smart Organization**
- Each question saved as a separate image
- Automatic matching of questions with mark schemes
- Topic-based folder structure
- JSON database tracking all metadata

## Installation

### Prerequisites

1. **Python 3.8+** (You have 3.12.3 ✓)
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
cd topicalforge
pip install -r requirements.txt --break-system-packages
```

Required packages:
- `selenium` - Web scraping
- `Pillow` - Image processing
- `PyMuPDF` - PDF parsing
- `pdf2image` - PDF to image conversion
- `watchdog` - File system monitoring

## Project Structure

```
topicalforge/
├── main.py              # Main orchestrator
├── config.py            # Configuration settings
├── downloader.py        # Selenium-based PDF downloader
├── slicer.py           # Question extractor
├── sorter.py           # UI for topic tagging
├── requirements.txt    # Python dependencies
├── data/
│   ├── pdfs/                  # Downloaded papers (auto-created)
│   ├── raw_questions/         # Extracted questions (auto-created)
│   ├── sorted_questions/      # Organized by topic (auto-created)
│   └── questions_db.json      # Metadata database
└── logs/
    ├── main.log
    ├── downloader.log
    ├── slicer.log
    └── sorter.log
```

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
Runs Downloader → Slicer → Sorter in parallel

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

## Troubleshooting

### Selenium/ChromeDriver Issues

**Error: "chromedriver not found"**
```bash
# Check if installed
which chromedriver

# If not found, install
sudo apt install chromium-chromedriver
```

**Error: "Chrome version mismatch"**
```bash
# Check Chrome version
google-chrome --version

# Install matching ChromeDriver from:
# https://chromedriver.chromium.org/downloads
```

### PDF Processing Issues

**Questions not detected properly**
- Check `logs/slicer.log` for details
- CIE formats are usually consistent, but some old papers may vary
- You can adjust question patterns in `config.py`

**Images too large/small**
- Adjust DPI in `slicer.py`: `mat = fitz.Matrix(2.0, 2.0)`
- Higher values = better quality but larger files

### Download Issues

**403 Forbidden errors**
- bestexamhelp.com has rate limiting
- Increase delays in `downloader.py`
- Run in non-headless mode to see what's happening

**PDFs not downloading**
- Check if site structure changed
- Verify URLs manually first
- Check `logs/downloader.log`

## Performance Tips

### Speed Up Processing

1. **Disable headless mode during setup** (easier debugging)
2. **Process subjects separately** for faster iteration
3. **Use multiple terminals**:
   ```bash
   # Terminal 1
   python3 downloader.py
   
   # Terminal 2  
   python3 slicer.py
   
   # Terminal 3
   python3 sorter.py
   ```

### Storage Considerations

- ~50MB per subject per year (PDFs)
- ~200MB for extracted questions (images)
- Use external drive if space is limited

## Future Enhancements (Not Yet Implemented)

- [ ] Mark scheme text extraction
- [ ] Automatic marks extraction from MS
- [ ] Question difficulty estimation
- [ ] Progress tracking & analytics
- [ ] AI-powered question generation
- [ ] Multi-board support (Edexcel, AQA, OCR)
- [ ] Native question solving interface
- [ ] Cloud sync

## License & Legal

This tool is for **personal educational use only**.

- Respects bestexamhelp.com's terms of use
- Does not redistribute copyrighted content
- Uses publicly available past papers
- Rate-limited to avoid server strain

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

**Happy studying! 📚✨**

Made with ❤️ for CIE students worldwide