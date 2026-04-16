"""
Base classes and source registry for TopicalForge.

HOW TO ADD A NEW SOURCE
-----------------------
1. Create a folder:  sources/<your_source_key>/
2. Inside it, create:
     __init__.py    -- calls register_source() at import time
     config.py      -- subjects dict + any setting overrides
     downloader.py  -- subclass of BaseDownloaderSource
     slicer.py      -- subclass of BaseSlicerSource

3. Import your source package at the bottom of THIS file so the registry
   picks it up automatically.

That is all. The workers and main.py never need to change.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# =============================================================================
# Base class: downloader source
# =============================================================================

class BaseDownloaderSource(ABC):
    """
    Knows how to turn a subject config into a list of (url, filename) pairs
    and how to decide whether a download actually succeeded.

    Subclass this for every website you want to support.
    """

    # ts is the name for the source shown in the menu
    label: str = "Unnamed source"

    @abstractmethod
    def generate_download_targets(self, subject_code: str, subject_cfg: dict) -> list[tuple[str, str]]:
        """
        Return a list of (url, filename_without_extension) pairs for every
        paper that plausibly exists for this subject.

        Parameters
        ----------
        subject_code : str
            The subject code key, e.g. "9709".
        subject_cfg : dict
            The subject entry from the source's config.SUBJECTS dict.

        Returns
        -------
        list of (url, base_filename) tuples, e.g.
            [("https://example.com/.../9709_s22_qp_11.pdf", "9709_s22_qp_11"), ...]
        """

    def post_download_check(self, pdf_path: str) -> bool:
        """
        Called after Selenium navigates to the URL.  The default
        implementation just checks whether the file appeared on disk.
        Override if you need to inspect the downloaded file further
        (e.g. to reject stub PDFs that are just error pages).
        """
        import os
        return os.path.exists(pdf_path)


# =============================================================================
# Base class: slicer source
# =============================================================================

class BaseSlicerSource(ABC):
    """
    Knows how to extract individual question slices from PDFs produced by a
    specific exam board / paper layout.

    Subclass this for every distinct paper layout you want to support.
    """

    label: str = "Unnamed slicer"

    @abstractmethod
    def extract_questions(self, pdf_path: str, raw_questions_dir: str) -> list[dict]:
        """
        Open the PDF at pdf_path, detect question boundaries, render each
        question as a PNG, and return a list of question records.

        Each record must contain at minimum:
            id           -- unique string, e.g. "9709_s22_qp_11_1"
            subject_code -- e.g. "9709"
            session      -- e.g. "s22"
            paper_num    -- e.g. "11"
            question_num -- e.g. "1"
            page_num     -- 1-indexed page where the question starts
            image_path   -- absolute path to the saved PNG
            paper_type   -- "qp" or "ms"

        QP records should also include:
            ms_image_path -- None initially, filled by the slicer after MS processing
            topic         -- None initially, filled by the sorter
            marks         -- None initially, may be filled later

        Returns an empty list if no questions were detected.
        """

    def is_mark_scheme(self, filename: str) -> bool:
        """
        Return True if this PDF filename is a mark scheme.
        The default implementation checks for '_ms_' in the name.
        Override if your naming convention differs.
        """
        return "_ms_" in filename


# =============================================================================
# Source registry
# =============================================================================

# Maps source_key -> {"downloader": BaseDownloaderSource, "slicer": BaseSlicerSource,
#                      "config": module, "label": str}
_REGISTRY: dict[str, dict] = {}


def register_source(
    key: str,
    label: str,
    downloader_cls: type[BaseDownloaderSource],
    slicer_cls: type[BaseSlicerSource],
    config_module,
):
    """
    Called from each source's __init__.py to register itself.

    Parameters
    ----------
    key            : unique snake_case identifier, e.g. "bestexamhelp_cie"
    label          : human-readable name shown in the menu
    downloader_cls : uninstantiated subclass of BaseDownloaderSource
    slicer_cls     : uninstantiated subclass of BaseSlicerSource
    config_module  : the source's config module (has SUBJECTS, and optionally
                     overrides for PAPER_TYPES, START_YEAR, END_YEAR, SESSIONS,
                     MIN_QUESTION_HEIGHT, MAX_QUESTION_NUMBER)
    """
    _REGISTRY[key] = {
        "label":          label,
        "downloader_cls": downloader_cls,
        "slicer_cls":     slicer_cls,
        "config":         config_module,
    }


def get_source(key: str) -> dict:
    """Return the registry entry for key, or raise KeyError."""
    if key not in _REGISTRY:
        raise KeyError(
            f"Source '{key}' is not registered. "
            f"Available sources: {list(_REGISTRY.keys())}"
        )
    return _REGISTRY[key]


def list_sources() -> list[tuple[str, str]]:
    """Return [(key, label), ...] for all registered sources, sorted by key."""
    return sorted((k, v["label"]) for k, v in _REGISTRY.items())


def resolve_source_config(source_cfg_module) -> dict:
    """
    Merge a source-level config module with global defaults.
    Source values take priority over globals.

    Returns a plain dict with keys:
        SUBJECTS, PAPER_TYPES, START_YEAR, END_YEAR, SESSIONS,
        MIN_QUESTION_HEIGHT, MAX_QUESTION_NUMBER
    """
    import config as global_cfg

    def _get(attr, default):
        return getattr(source_cfg_module, attr, default)

    return {
        "SUBJECTS":             _get("SUBJECTS", {}),
        "PAPER_TYPES":          _get("PAPER_TYPES",          global_cfg.DEFAULT_PAPER_TYPES),
        "START_YEAR":           _get("START_YEAR",           global_cfg.DEFAULT_START_YEAR),
        "END_YEAR":             _get("END_YEAR",             global_cfg.DEFAULT_END_YEAR),
        "SESSIONS":             _get("SESSIONS",             global_cfg.DEFAULT_SESSIONS),
        "MIN_QUESTION_HEIGHT":  _get("MIN_QUESTION_HEIGHT",  global_cfg.DEFAULT_MIN_QUESTION_HEIGHT),
        "MAX_QUESTION_NUMBER":  _get("MAX_QUESTION_NUMBER",  global_cfg.DEFAULT_MAX_QUESTION_NUMBER),
    }


# =============================================================================
# Auto-import all source packages so they can call register_source()
# Add a new import here when you create a new source folder.
# =============================================================================

import sources.bestexamhelp_cie  # noqa: E402, F401
