"""
this is the global config
anything specific to a source lives in sources/<source_key>/config.py and will override these defaults
"""

import os

# =============================================================================
# Global download defaults
# These are used by any source that does not supply its own value.
# =============================================================================
DEFAULT_PAPER_TYPES  = ["qp", "ms"]   # question paper + mark scheme code
DEFAULT_START_YEAR   = 2009
DEFAULT_END_YEAR     = 2025
DEFAULT_SESSIONS     = ["s", "w"]     # s = summer, w = winter

# =============================================================================
# Global slicer defaults
# =============================================================================
# Minimum height (pts) a question slice must be to count as a real question.
# Raise this if you are getting too many false-positive splits.
DEFAULT_MIN_QUESTION_HEIGHT = 40

# Any detected question number above this is treated as a false positive
# (e.g. "20 cm" or "30 marks" annotations in the margin).
DEFAULT_MAX_QUESTION_NUMBER = 30

# =============================================================================
# Global watchdog (ts watches folders for new files to process) 
# =============================================================================
WATCH_INTERVAL   = 2

# =============================================================================
# Directory structure
# All workers and sources use these paths -- do not redefine them per source.
# =============================================================================
BASE_DIR             = os.path.dirname(os.path.abspath(__file__))
DATA_DIR             = os.path.join(BASE_DIR, "data")
PDF_DIR              = os.path.join(DATA_DIR, "pdfs")
RAW_QUESTIONS_DIR    = os.path.join(DATA_DIR, "raw_questions")
SORTED_QUESTIONS_DIR = os.path.join(DATA_DIR, "sorted_questions")
LOGS_DIR             = os.path.join(BASE_DIR, "logs")

for _dir in [PDF_DIR, RAW_QUESTIONS_DIR, SORTED_QUESTIONS_DIR, LOGS_DIR]:
    os.makedirs(_dir, exist_ok=True)
