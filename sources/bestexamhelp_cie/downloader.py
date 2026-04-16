"""
sources/bestexamhelp_cie/downloader.py

Downloader adapter for bestexamhelp.com / CIE A-Level papers.

Generates all plausible (url, filename) pairs for a given subject, based on
the source config (years, sessions, paper types, variants).

The URL pattern used by bestexamhelp is:
    https://bestexamhelp.com/exam/cambridge-international-a-level/
        <subject-name>-<subject-code>/<year>/<paper-code>.pdf

For example:
    https://bestexamhelp.com/exam/cambridge-international-a-level/
        mathematics-9709/2022/9709_s22_qp_11.pdf
"""

import logging
from sources import BaseDownloaderSource

logger = logging.getLogger(__name__)

BASE_URL = "https://bestexamhelp.com/exam/cambridge-international-a-level/"


class BestExamHelpCIEDownloader(BaseDownloaderSource):

    label = "BestExamHelp (CIE A-Level)"

    def __init__(self, source_config: dict):
        """
        Parameters
        ----------
        source_config : dict
            The merged config dict produced by sources.resolve_source_config().
            Expected keys: SUBJECTS, PAPER_TYPES, START_YEAR, END_YEAR,
                           SESSIONS, and the CIE-specific VARIANTS list from
                           the source's own config module.
        """
        self._cfg = source_config

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _generate_codes(self, subject_code: str, subject_cfg: dict) -> list[tuple[str, str]]:
        """
        Return (url, base_filename) pairs for every plausible paper.

        CIE paper filename pattern:
            <subject_code>_<session><yy>_<paper_type>_<paper_num><variant>
        e.g.  9709_s22_qp_11
        """
        cfg      = self._cfg
        papers   = subject_cfg["papers"]
        variants = cfg.get("VARIANTS", [1, 2, 3])
        targets: list[tuple[str, str]] = []

        for year in range(cfg["START_YEAR"], cfg["END_YEAR"] + 1):
            yy   = str(year)[2:]   # "2022" -> "22"
            full = str(year)       # "2022"

            for session in cfg["SESSIONS"]:
                for paper_num in papers:
                    for variant in variants:
                        for paper_type in cfg["PAPER_TYPES"]:
                            code = (
                                f"{subject_code}_{session}{yy}"
                                f"_{paper_type}_{paper_num}{variant}"
                            )
                            url = (
                                f"{BASE_URL}"
                                f"{subject_cfg['name']}-{subject_code}/"
                                f"{full}/{code}.pdf"
                            )
                            targets.append((url, code))

        logger.info(
            "Generated %d targets for %s (%s)",
            len(targets),
            subject_cfg["label"],
            subject_code,
        )
        return targets

    # -------------------------------------------------------------------------
    # BaseDownloaderSource interface
    # -------------------------------------------------------------------------

    def generate_download_targets(
        self, subject_code: str, subject_cfg: dict
    ) -> list[tuple[str, str]]:
        return self._generate_codes(subject_code, subject_cfg)
