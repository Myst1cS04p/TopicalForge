#!/usr/bin/env python3
"""
Slicer Worker  Extracts individual questions from PDF papers as images.

Now processes both question papers (qp) AND mark schemes (ms).
MS slices are stored in the DB and automatically linked to their
corresponding QP entry by (subject_code, session, paper_num, question_num).

Don't try reading this unless you want to have an existential crisis.
"""

import os
import re
import json
import time
import logging
from pathlib import Path

import fitz
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [SLICER] - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(config.LOGS_DIR, "slicer.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Detection helpers
# ==============================================================================

def _is_valid_question_block(block_text: str, q_num: int, x0: float, page_width: float) -> bool:
    if q_num > config.MAX_QUESTION_NUMBER or q_num == 0:
        return False

    unit_pattern = re.compile(
        r"^\d+\s*(cm|mm\b|m\b|km|kg|g\b|N\b|J\b|W\b|Pa|mol|K\b|degrees|%|marks?)\b",
        re.IGNORECASE,
    )
    if unit_pattern.match(block_text.strip()):
        return False

    # Must sit in the left margin
    if page_width > 0 and x0 > page_width * 0.15:
        return False

    return True


def _blocks_to_question_positions(page: fitz.Page) -> dict[str, float]:
    positions: dict[str, float] = {}
    page_width = page.rect.width

    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text, *_ = block
        stripped = text.strip()
        if not stripped:
            continue

        match = re.match(r"^(\d{1,2})(?:\s|$)", stripped)
        if not match:
            continue

        q_num = int(match.group(1))
        q_str = match.group(1)

        if not _is_valid_question_block(stripped, q_num, x0, page_width):
            continue

        if q_str not in positions or y0 < positions[q_str]:
            positions[q_str] = y0

    return positions


# ==============================================================================
# Core extractor
# ==============================================================================

class QuestionExtractor:
    def __init__(self):
        self.db_path = os.path.join(config.DATA_DIR, "questions_db.json")
        self.question_db: dict = {}
        self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path) as f:
                self.question_db = json.load(f)
            total = sum(len(v.get("questions", [])) for v in self.question_db.values())
            logger.info("Loaded DB: %d PDFs, %d questions", len(self.question_db), total)

    def _save_db(self):
        with open(self.db_path, "w") as f:
            json.dump(self.question_db, f, indent=2)

    # ==========================================================================
    # Rendering 
    # ==========================================================================

    @staticmethod
    def _render_region(page: fitz.Page, y_start: float, y_end: float) -> Image.Image:
        rect = page.rect
        clip = fitz.Rect(0, max(0, y_start), rect.width, min(rect.height, y_end))
        mat  = fitz.Matrix(2.0, 2.0)
        pix  = page.get_pixmap(matrix=mat, clip=clip)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    @staticmethod
    def _stitch_images(images: list[Image.Image]) -> Image.Image:
        if len(images) == 1:
            return images[0]
        total_h = sum(img.height for img in images)
        width   = max(img.width for img in images)
        canvas  = Image.new("RGB", (width, total_h), "white")
        y = 0
        for img in images:
            canvas.paste(img, (0, y))
            y += img.height
        return canvas

    # ==========================================================================
    # MS linking 
    # ==========================================================================

    def _link_ms_to_qp(self, subject_code: str, session: str, paper_num: str,
                        q_str: str, ms_img_path: str):
        """Find the matching QP entry and write ms_image_path onto it."""
        for pdf_name, pdf_data in self.question_db.items():
            if "_qp_" not in pdf_name:
                continue
            for q in pdf_data.get("questions", []):
                if (q.get("subject_code") == subject_code
                        and q.get("session") == session
                        and q.get("paper_num") == paper_num
                        and q.get("question_num") == q_str):
                    q["ms_image_path"] = ms_img_path
                    return

    # ==========================================================================
    # PDF processing
    # ==========================================================================

    def process_pdf(self, pdf_path: str):
        filename = os.path.basename(pdf_path)

        if filename in self.question_db:
            logger.info("Already processed: %s", filename)
            return

        logger.info("Processing: %s", filename)

        parts = filename.replace(".pdf", "").split("_")
        if len(parts) < 4:
            logger.warning("Unexpected filename format: %s", filename)
            return

        subject_code = parts[0]
        session      = parts[1]
        paper_type   = parts[2]   # "qp" or "ms"
        paper_num    = parts[3]
        is_ms        = (paper_type == "ms")

        try:
            doc = fitz.open(pdf_path)
        except Exception as exc:
            logger.error("Cannot open %s: %s", filename, exc)
            return

        # Collect question positions across all pages
        all_positions: dict[str, list[tuple[int, float]]] = {}
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            for q_str, y0 in _blocks_to_question_positions(page).items():
                all_positions.setdefault(q_str, []).append((page_idx, y0))

        if not all_positions:
            logger.warning("No questions detected in %s", filename)
            doc.close()
            self.question_db[filename] = {"processed": True, "questions": [], "total_questions": 0}
            self._save_db()
            return

        sorted_q_nums = sorted(all_positions.keys(), key=lambda x: int(x))
        extracted: list[dict] = []
        seen_ids: set[str] = set()

        for i, q_str in enumerate(sorted_q_nums):
            start_page_idx, start_y = all_positions[q_str][0]

            if i + 1 < len(sorted_q_nums):
                next_q_str = sorted_q_nums[i + 1]
                end_page_idx, end_y = all_positions[next_q_str][0]
            else:
                end_page_idx = len(doc) - 1
                end_y        = doc[end_page_idx].rect.height

            if start_page_idx == end_page_idx and end_y - start_y < config.MIN_QUESTION_HEIGHT:
                logger.debug("Skipping Q%s in %s - slice too thin", q_str, filename)
                continue

            images: list[Image.Image] = []
            try:
                for p_idx in range(start_page_idx, end_page_idx + 1):
                    page   = doc[p_idx]
                    y_from = start_y if p_idx == start_page_idx else 0
                    y_to   = end_y   if p_idx == end_page_idx   else page.rect.height
                    images.append(self._render_region(page, y_from, y_to))

                combined    = self._stitch_images(images)
                question_id = f"{filename.replace('.pdf', '')}_{q_str}"

                if question_id in seen_ids:
                    continue
                seen_ids.add(question_id)

                img_path = os.path.join(config.RAW_QUESTIONS_DIR, f"{question_id}.png")
                combined.save(img_path)

                if is_ms:
                    extracted.append({
                        "id":           question_id,
                        "subject_code": subject_code,
                        "session":      session,
                        "paper_num":    paper_num,
                        "question_num": q_str,
                        "page_num":     start_page_idx + 1,
                        "image_path":   img_path,
                    })
                    self._link_ms_to_qp(subject_code, session, paper_num, q_str, img_path)
                else:
                    extracted.append({
                        "id":            question_id,
                        "subject_code":  subject_code,
                        "session":       session,
                        "paper_num":     paper_num,
                        "question_num":  q_str,
                        "page_num":      start_page_idx + 1,
                        "image_path":    img_path,
                        "ms_image_path": None,   # filled when MS is processed
                        "topic":         None,
                        "marks":         None,
                    })

                logger.info("Extracted Q%s from %s", q_str, filename)

            except Exception as exc:
                logger.error("Failed Q%s in %s: %s", q_str, filename, exc)

        doc.close()

        self.question_db[filename] = {
            "processed":       True,
            "questions":       extracted,
            "total_questions": len(extracted),
        }
        self._save_db()
        logger.info("Completed %s: %d slices", filename, len(extracted))

        # If this was a QP and its MS was already processed, back-link now.
        if not is_ms:
            ms_filename = filename.replace("_qp_", "_ms_")
            if ms_filename in self.question_db:
                logger.info("MS already in DB - back-linking: %s", ms_filename)
                for ms_q in self.question_db[ms_filename].get("questions", []):
                    self._link_ms_to_qp(
                        subject_code, session, paper_num,
                        ms_q["question_num"], ms_q["image_path"],
                    )
                self._save_db()


# ==============================================================================
# Watchdog
# ==============================================================================

class PDFWatcher(FileSystemEventHandler):
    def __init__(self, extractor: QuestionExtractor):
        self.extractor  = extractor
        self.processing: set[str] = set()

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".pdf"):
            return
        if event.src_path in self.processing:
            return
        self.processing.add(event.src_path)
        time.sleep(2)
        logger.info("New PDF: %s", os.path.basename(event.src_path))
        self.extractor.process_pdf(event.src_path)
        self.processing.discard(event.src_path)


# ==============================================================================
# Entry point
# ==============================================================================

def run_slicer():
    logger.info("Slicer started")
    extractor = QuestionExtractor()

    existing = sorted(Path(config.PDF_DIR).glob("*.pdf"))
    if existing:
        logger.info("Processing %d existing PDFs", len(existing))
        for pdf_path in existing:
            extractor.process_pdf(str(pdf_path))
    else:
        logger.info("No existing PDFs found")

    handler  = PDFWatcher(extractor)
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


if __name__ == "__main__":
    run_slicer()