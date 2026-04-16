"""
sources/bestexamhelp_cie/slicer.py

Slicer adapter for CIE A-Level papers downloaded from bestexamhelp.com.

CIE papers number questions in the left margin with a plain integer, optionally
followed by a space and the question text.  This module detects those margin
numbers, slices the page vertically between consecutive question starts,
renders each slice as a PNG, and returns structured question records.

If you are adding support for a board whose papers use a different layout
(e.g. numbered bullets in the body text, or "(a)" / "(b)" sub-questions as
top-level entries), create a new slicer in your own source folder instead of
modifying this one.
"""

import os
import re
import logging
from typing import Optional

import fitz
from PIL import Image

from sources import BaseSlicerSource

logger = logging.getLogger(__name__)


# =============================================================================
# Low-level detection helpers
# These are module-level so they can be tested independently of the class.
# =============================================================================

def _is_valid_question_block(
    block_text: str,
    q_num: int,
    x0: float,
    page_width: float,
    max_q_num: int,
) -> bool:
    """
    Return True if a text block that starts with an integer looks like a real
    question number rather than a false positive.

    False-positive patterns we reject:
    - Numbers that exceed max_q_num  (unrealistically high question count)
    - Numbers immediately followed by a unit  (e.g. "20 cm", "30 marks")
    - Numbers whose left edge is not in the left margin (> 15% of page width)
    """
    if q_num > max_q_num or q_num == 0:
        return False

    unit_pattern = re.compile(
        r"^\d+\s*(cm|mm\b|m\b|km|kg|g\b|N\b|J\b|W\b|Pa|mol|K\b|degrees|%|marks?)\b",
        re.IGNORECASE,
    )
    if unit_pattern.match(block_text.strip()):
        return False

    # Question numbers must sit in the left margin.
    if page_width > 0 and x0 > page_width * 0.15:
        return False

    return True


def _blocks_to_question_positions(
    page: fitz.Page,
    max_q_num: int,
) -> dict[str, float]:
    """
    Scan all text blocks on a page and return a mapping of
    question_number_string -> y_coordinate_of_first_occurrence.

    Only the topmost occurrence of each question number is kept, so that a
    question spanning multiple pages still anchors to its first line.
    """
    positions: dict[str, float] = {}
    page_width = page.rect.width

    for block in page.get_text("blocks"):
        x0, y0, _x1, _y1, text, *_ = block
        stripped = text.strip()
        if not stripped:
            continue

        match = re.match(r"^(\d{1,2})(?:\s|$)", stripped)
        if not match:
            continue

        q_num = int(match.group(1))
        q_str = match.group(1)

        if not _is_valid_question_block(stripped, q_num, x0, page_width, max_q_num):
            continue

        # Keep only the topmost y for each question number.
        if q_str not in positions or y0 < positions[q_str]:
            positions[q_str] = y0

    return positions


# =============================================================================
# CIE slicer class
# =============================================================================

class BestExamHelpCIESlicer(BaseSlicerSource):

    label = "CIE A-Level (bestexamhelp layout)"

    def __init__(self, source_config: dict):
        """
        Parameters
        ----------
        source_config : dict
            Merged config from sources.resolve_source_config().
            Used keys: MIN_QUESTION_HEIGHT, MAX_QUESTION_NUMBER.
        """
        self._min_height = source_config["MIN_QUESTION_HEIGHT"]
        self._max_q_num  = source_config["MAX_QUESTION_NUMBER"]

    # -------------------------------------------------------------------------
    # Rendering helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _render_region(
        page: fitz.Page,
        y_start: float,
        y_end: float,
    ) -> Image.Image:
        """Render a vertical strip of *page* from y_start to y_end at 2x scale."""
        rect = page.rect
        clip = fitz.Rect(0, max(0, y_start), rect.width, min(rect.height, y_end))
        mat  = fitz.Matrix(2.0, 2.0)
        pix  = page.get_pixmap(matrix=mat, clip=clip)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    @staticmethod
    def _stitch_images(images: list[Image.Image]) -> Image.Image:
        """Vertically concatenate a list of images into one canvas."""
        if len(images) == 1:
            return images[0]
        total_h = sum(img.height for img in images)
        width   = max(img.width  for img in images)
        canvas  = Image.new("RGB", (width, total_h), "white")
        y = 0
        for img in images:
            canvas.paste(img, (0, y))
            y += img.height
        return canvas

    # -------------------------------------------------------------------------
    # Filename parsing
    # -------------------------------------------------------------------------

    @staticmethod
    def _parse_filename(filename: str) -> Optional[tuple[str, str, str, str]]:
        """
        Parse a CIE PDF filename into (subject_code, session, paper_type, paper_num).

        Expected format: <subject_code>_<session><yy>_<paper_type>_<paper_num>.pdf
        e.g. "9709_s22_qp_11.pdf" -> ("9709", "s22", "qp", "11")

        Returns None if the filename does not match the expected pattern.
        """
        stem  = filename.replace(".pdf", "")
        parts = stem.split("_")
        if len(parts) < 4:
            return None
        return parts[0], parts[1], parts[2], parts[3]

    # -------------------------------------------------------------------------
    # BaseSlicerSource interface
    # -------------------------------------------------------------------------

    def extract_questions(
        self,
        pdf_path: str,
        raw_questions_dir: str,
    ) -> list[dict]:
        """
        Extract question slices from a CIE past-paper PDF.

        Returns a list of question record dicts (see BaseSlicerSource docstring
        for the required fields).  Returns an empty list on any unrecoverable
        error so the caller can log and move on.
        """
        filename = os.path.basename(pdf_path)
        parsed   = self._parse_filename(filename)

        if parsed is None:
            logger.warning("Skipping unrecognised filename format: %s", filename)
            return []

        subject_code, session, paper_type, paper_num = parsed
        is_ms = (paper_type == "ms")

        # ------------------------------------------------------------------
        # Open PDF and collect question start positions across all pages.
        # ------------------------------------------------------------------
        try:
            doc = fitz.open(pdf_path)
        except Exception as exc:
            logger.error("Cannot open %s: %s", filename, exc)
            return []

        # all_positions maps question_num_str -> [(page_idx, y0), ...]
        all_positions: dict[str, list[tuple[int, float]]] = {}
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            for q_str, y0 in _blocks_to_question_positions(page, self._max_q_num).items():
                all_positions.setdefault(q_str, []).append((page_idx, y0))

        if not all_positions:
            logger.warning("No questions detected in %s", filename)
            doc.close()
            return []

        sorted_q_nums = sorted(all_positions.keys(), key=lambda x: int(x))
        extracted: list[dict] = []
        seen_ids: set[str]    = set()

        for i, q_str in enumerate(sorted_q_nums):
            start_page_idx, start_y = all_positions[q_str][0]

            # Determine where this question ends (start of the next one).
            if i + 1 < len(sorted_q_nums):
                next_q_str                 = sorted_q_nums[i + 1]
                end_page_idx, end_y        = all_positions[next_q_str][0]
            else:
                end_page_idx = len(doc) - 1
                end_y        = doc[end_page_idx].rect.height

            # Reject slices that are too thin -- likely false positives.
            if (
                start_page_idx == end_page_idx
                and end_y - start_y < self._min_height
            ):
                logger.debug("Skipping Q%s in %s -- slice too thin", q_str, filename)
                continue

            # ------------------------------------------------------------------
            # Render and stitch the pages covered by this question.
            # ------------------------------------------------------------------
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

                img_path = os.path.join(raw_questions_dir, f"{question_id}.png")
                combined.save(img_path)

                # Build the record.  QP and MS records differ slightly.
                base_record = {
                    "id":           question_id,
                    "subject_code": subject_code,
                    "session":      session,
                    "paper_num":    paper_num,
                    "question_num": q_str,
                    "page_num":     start_page_idx + 1,
                    "image_path":   img_path,
                    "paper_type":   paper_type,
                }

                if is_ms:
                    extracted.append(base_record)
                else:
                    extracted.append({
                        **base_record,
                        "ms_image_path": None,   # filled once the MS is processed
                        "topic":         None,   # filled by the sorter
                        "marks":         None,
                    })

                logger.info("Extracted Q%s from %s", q_str, filename)

            except Exception as exc:
                logger.error("Failed Q%s in %s: %s", q_str, filename, exc)

        doc.close()
        logger.info("Completed %s: %d slices", filename, len(extracted))
        return extracted
