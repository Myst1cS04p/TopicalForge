"""
sources/bestexamhelp_cie/__init__.py

Registers the BestExamHelp / CIE A-Level source with the global source
registry.  This file is imported automatically by sources/__init__.py.
"""

from sources import register_source, resolve_source_config
from sources.bestexamhelp_cie import config as _cfg
from sources.bestexamhelp_cie.downloader import BestExamHelpCIEDownloader
from sources.bestexamhelp_cie.slicer import BestExamHelpCIESlicer

SOURCE_KEY   = "bestexamhelp_cie"
SOURCE_LABEL = "BestExamHelp -- CIE A-Level"

# Merge source overrides with global defaults once at import time.
_merged_cfg = resolve_source_config(_cfg)

# Inject the CIE-specific VARIANTS list (not part of the global defaults).
_merged_cfg["VARIANTS"] = getattr(_cfg, "VARIANTS", [1, 2, 3])

register_source(
    key            = SOURCE_KEY,
    label          = SOURCE_LABEL,
    downloader_cls = lambda: BestExamHelpCIEDownloader(_merged_cfg),
    slicer_cls     = lambda: BestExamHelpCIESlicer(_merged_cfg),
    config_module  = _cfg,
)
