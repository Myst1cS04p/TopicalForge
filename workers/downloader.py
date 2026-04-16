"""
This is the generic or base download worker
For all my OOP bros this is like an interface or abstract class
"""

import os
import time
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import config
from sources import get_source, resolve_source_config

logger = logging.getLogger(__name__)


# =============================================================================
# Driver setup
# =============================================================================

def _build_driver() -> webdriver.Chrome:
    """Initialise and return a Chrome WebDriver configured for PDF downloads."""
    chrome_options = Options()
    if config.HEADLESS_MODE:
        chrome_options.add_argument("--headless")
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
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome driver initialised")
        return driver
    except Exception as exc:
        logger.error("Failed to initialise Chrome driver: %s", exc)
        raise


# =============================================================================
# Per-file download
# =============================================================================

def _download_one(
    driver: webdriver.Chrome,
    source_adapter,
    url: str,
    base_filename: str,
) -> bool:
    """
    Attempt to download a single PDF.

    Returns True if the file is already on disk or was successfully downloaded,
    False otherwise.
    """
    pdf_path = os.path.join(config.PDF_DIR, f"{base_filename}.pdf")

    if os.path.exists(pdf_path):
        logger.info("Already exists: %s.pdf", base_filename)
        return True

    try:
        logger.info("Attempting: %s", base_filename)
        driver.get(url)
        time.sleep(3)
        if source_adapter.post_download_check(pdf_path):
            logger.info("Downloaded: %s.pdf", base_filename)
            return True
    except Exception as exc:
        logger.debug("URL failed (%s): %s", base_filename, exc)

    logger.warning("Could not download: %s", base_filename)
    return False


# =============================================================================
# Entry point
# =============================================================================

def run_downloader(source_key: str):
    """
    Run the full download loop for the given source.

    Parameters
    ----------
    source_key : str
        Key into the source registry, e.g. "bestexamhelp_cie".
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [DOWNLOADER] - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(config.LOGS_DIR, "downloader.log")),
            logging.StreamHandler(),
        ],
    )

    entry          = get_source(source_key)
    source_adapter = entry["downloader_cls"]() 
    source_cfg     = resolve_source_config(entry["config"])
    subjects       = source_cfg["SUBJECTS"]

    logger.info("Downloader started -- source: %s", entry["label"])
    logger.info("PDFs will be saved to: %s", config.PDF_DIR)

    driver = _build_driver()

    try:
        for subject_code, subject_cfg in subjects.items():
            logger.info(
                "Starting subject: %s (%s)",
                subject_cfg["label"],
                subject_code,
            )
            targets   = source_adapter.generate_download_targets(subject_code, subject_cfg)
            successes = 0

            for url, base_filename in targets:
                if _download_one(driver, source_adapter, url, base_filename):
                    successes += 1
                time.sleep(0.5)

            logger.info(
                "Finished %s: %d/%d downloaded",
                subject_code,
                successes,
                len(targets),
            )

        logger.info("Downloader complete")

    except KeyboardInterrupt:
        logger.info("Downloader interrupted")
    except Exception as exc:
        logger.error("Downloader error: %s", exc, exc_info=True)
    finally:
        driver.quit()
        logger.info("Chrome driver closed")
