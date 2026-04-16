"""
This is the generic or base slicer worker
For all my OOP bros this is like an interface or abstract class
"""

import os
import json
import time
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import config
from sources import get_source, resolve_source_config

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(config.DATA_DIR, "questions_db.json")


# =============================================================================
# Database helpers
# =============================================================================

def _load_db() -> dict:
    if os.path.exists(DB_PATH):
        with open(DB_PATH) as f:
            db = json.load(f)
        total = sum(len(v.get("questions", [])) for v in db.values())
        logger.info("Loaded DB: %d PDFs, %d questions", len(db), total)
        return db
    return {}


def _save_db(db: dict):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


# =============================================================================
# MS <-> QP back-linking
# =============================================================================

def _link_ms_to_qp(
    db: dict,
    subject_code: str,
    session: str,
    paper_num: str,
    q_str: str,
    ms_img_path: str,
):
    """
    Find the matching QP question record in *db* and write ms_image_path onto
    it.  Matching is done on (subject_code, session, paper_num, question_num).
    """
    for pdf_name, pdf_data in db.items():
        if "_qp_" not in pdf_name:
            continue
        for q in pdf_data.get("questions", []):
            if (
                q.get("subject_code") == subject_code
                and q.get("session")      == session
                and q.get("paper_num")    == paper_num
                and q.get("question_num") == q_str
            ):
                q["ms_image_path"] = ms_img_path
                return


# =============================================================================
# Core processing
# =============================================================================

def _process_pdf(pdf_path: str, slicer_adapter, db: dict):
    """
    Extract questions from *pdf_path* using *slicer_adapter*, store results in
    *db*, and handle MS back-linking.  Skips files already present in the DB.
    """
    filename = os.path.basename(pdf_path)

    if filename in db:
        logger.info("Already processed: %s", filename)
        return

    logger.info("Processing: %s", filename)

    questions = slicer_adapter.extract_questions(pdf_path, config.RAW_QUESTIONS_DIR)
    is_ms     = slicer_adapter.is_mark_scheme(filename)

    # Store in DB regardless of whether questions were found.
    db[filename] = {
        "processed":       True,
        "questions":       questions,
        "total_questions": len(questions),
    }
    _save_db(db)

    if not questions:
        logger.warning("No questions extracted from: %s", filename)
        return

    # ------------------------------------------------------------------
    # MS back-linking -- run regardless of which side arrived first.
    # ------------------------------------------------------------------
    if is_ms:
        # MS detected
        for ms_q in questions:
            _link_ms_to_qp(
                db,
                ms_q["subject_code"],
                ms_q["session"],
                ms_q["paper_num"],
                ms_q["question_num"],
                ms_q["image_path"],
            )
        _save_db(db)

    else:
        # QP detected
        ms_filename = filename.replace("_qp_", "_ms_")
        if ms_filename in db:
            logger.info("MS already in DB -- back-linking: %s", ms_filename)
            for ms_q in db[ms_filename].get("questions", []):
                _link_ms_to_qp(
                    db,
                    ms_q["subject_code"],
                    ms_q["session"],
                    ms_q["paper_num"],
                    ms_q["question_num"],
                    ms_q["image_path"],
                )
            _save_db(db)


# =============================================================================
# Watchdog handler
# =============================================================================

class _PDFWatcher(FileSystemEventHandler):
    def __init__(self, slicer_adapter, db: dict):
        self._slicer  = slicer_adapter
        self._db      = db
        self._in_progress: set[str] = set()

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".pdf"):
            return
        if event.src_path in self._in_progress:
            return
        self._in_progress.add(event.src_path)
        time.sleep(2)   # wait for the file to finish writing
        logger.info("New PDF detected: %s", os.path.basename(event.src_path))
        _process_pdf(event.src_path, self._slicer, self._db)
        self._in_progress.discard(event.src_path)


# =============================================================================
# Entry point
# =============================================================================

def run_slicer(source_key: str):
    """
    Run the slicer worker for the given source.

    Parameters
    ----------
    source_key : str
        Key into the source registry, e.g. "bestexamhelp_cie".
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [SLICER] - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(config.LOGS_DIR, "slicer.log")),
            logging.StreamHandler(),
        ],
    )

    entry          = get_source(source_key)
    slicer_adapter = entry["slicer_cls"]()   # factory lambda from source __init__.py

    logger.info("Slicer started -- source: %s", entry["label"])

    db = _load_db()

    # Process any PDFs that already exist in the download directory.
    existing = sorted(Path(config.PDF_DIR).glob("*.pdf"))
    if existing:
        logger.info("Processing %d existing PDFs", len(existing))
        for pdf_path in existing:
            _process_pdf(str(pdf_path), slicer_adapter, db)
    else:
        logger.info("No existing PDFs found -- watching for new ones")

    # Start watchdog to handle PDFs arriving from the downloader.
    handler  = _PDFWatcher(slicer_adapter, db)
    observer = Observer()
    observer.schedule(handler, config.PDF_DIR, recursive=False)
    observer.start()
    logger.info("Watching: %s", config.PDF_DIR)

    try:
        while True:
            time.sleep(config.WATCH_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Slicer interrupted")
        observer.stop()

    observer.join()
    logger.info("Slicer stopped")
