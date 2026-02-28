#!/usr/bin/env python3
"""
Downloader Worker 
Ts is what downloads the papers off of the interwebs using Selenium. It generates all plausible paper codes based on the subjects, years, sessions, and paper types defined in config.py, then attempts to download each one from the constructed URL. It handles retries and logs successes and failures.
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [DOWNLOADER] - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(config.LOGS_DIR, "downloader.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

BASE_URL = "https://bestexamhelp.com/exam/cambridge-international-a-level/"


class PaperDownloader:
    def __init__(self):
        self._setup_driver()

    # =========================================================================================
    # Driver
    # =========================================================================================
    def _setup_driver(self):
        chrome_options = Options()
        if config.HEADLESS_MODE:
            chrome_options.add_argument("--headless") # Makes chrome invisible
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": config.PDF_DIR,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
            },
        )
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver initialised")
        except Exception as exc:
            logger.error("Failed to initialise Chrome driver: %s", exc)
            raise

    # =========================================================================================
    # Code generation
    # =========================================================================================
    def _generate_paper_codes(self, subject_code: str) -> list[str]:
        """Return every plausible paper code for *subject_code*."""
        subject  = config.SUBJECTS[subject_code] # Loads subject data shi from the config
        papers   = subject["papers"] # Picking out the papers to grab, so like P1, P2, P3 etc. depending on the subject
        codes: list[str] = []

        # Don't worry abt this, it just loops shit and generates p codes, and I don't care to explain it.
        for year in range(config.START_YEAR, config.END_YEAR + 1):
            yy = str(year)[2:]  # Grab last two characters of the year string e.g. 2024 becomes "24"
            for session in config.SESSIONS:
                for variant in range(1, 4):      # variants 1, 2, 3 - no clue why I didn't put this in config.py, but whatever
                    for paper_num in papers:
                        for paper_type in config.PAPER_TYPES:
                            code = f"{subject_code}_{session}{yy}_{paper_type}_{paper_num}{variant}"
                            codes.append(code)

        logger.info(
            "Generated %d paper codes for %s",
            len(codes),
            subject["label"],
        )
        return codes

    # =========================================================================================
    # Download
    # =========================================================================================
    def _download_paper(self, subject_code: str, paper_code: str) -> bool:
        pdf_path = os.path.join(config.PDF_DIR, f"{paper_code}.pdf")
        if os.path.exists(pdf_path):
            logger.info("Already exists: %s.pdf", paper_code)
            return True

        subject = config.SUBJECTS[subject_code]
        # Extracts full year from code  e.g. "9709_s22_qp_11" gets "2022"
        try:
            year = "20" + paper_code.split("_")[1][1:3]
        except (IndexError, ValueError):
            logger.warning("Cannot parse year from code: %s", paper_code) # Big fk up somewhere in the code
            return False

        url = (
            f"{BASE_URL}"
            f"{subject['name']}-{subject_code}/"
            f"{year}/{paper_code}.pdf"
        )

        # Downloading shi, don't touch
        try:
            logger.info("Attempting: %s", paper_code)
            self.driver.get(url)
            time.sleep(3)
            if os.path.exists(pdf_path):
                logger.info("Downloaded: %s.pdf", paper_code)
                return True
        except Exception as exc:
            logger.debug("URL failed (%s): %s", paper_code, exc)

        logger.warning("Could not download: %s", paper_code)
        return False

    # =========================================================================================
    # Subject / main loop (Please don't touch, unless you wanna get touched)
    # =========================================================================================
    def download_subject(self, subject_code: str):
        subject = config.SUBJECTS[subject_code]
        logger.info("Starting download for %s (%s)", subject["label"], subject_code)
        codes     = self._generate_paper_codes(subject_code)
        successes = 0
        for code in codes:
            if self._download_paper(subject_code, code):
                successes += 1
            time.sleep(0.5)
        logger.info(
            "Finished %s: %d/%d downloaded",
            subject_code,
            successes,
            len(codes),
        )

    def run(self):
        try:
            logger.info("Downloader started")
            for subject_code in config.SUBJECTS:
                self.download_subject(subject_code)
            logger.info("Downloader complete")
        except KeyboardInterrupt:
            logger.info("Downloader interrupted")
        except Exception as exc:
            logger.error("Downloader error: %s", exc, exc_info=True)
        finally:
            self.driver.quit()
            logger.info("Chrome driver closed")


if __name__ == "__main__":
    PaperDownloader().run()