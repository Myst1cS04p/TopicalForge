#!/usr/bin/env python3
"""
TopicalForge | Main orchestrator.
Runs Downloader, Slicer, and Sorter workers.
"""

import os
import sys
import time
import logging
import threading

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [MAIN] - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(config.LOGS_DIR, "main.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

HEADER = """
╔═══════════════════════════════════════════════════════╗
║     TopicalForge — CIE A-Level Past Paper Parser      ║
╚═══════════════════════════════════════════════════════╝
"""

MENU = """\
  1  Full pipeline  (Downloader + Slicer + Sorter)
  2  Downloader only
  3  Slicer only
  4  Sorter only
  5  Slicer + Sorter  (PDFs already downloaded)
  0  Exit
"""


def _check_dependencies() -> bool:
    logger.info("Checking dependencies…")
    missing = []
    for mod, pkg in [("selenium", "selenium"), ("PIL", "Pillow"),
                     ("fitz", "PyMuPDF"), ("watchdog", "watchdog")]:
        try:
            __import__("PIL" if mod == "PIL" else mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        logger.error("Missing: %s  ->  pip install %s",
                     ", ".join(missing), " ".join(missing))
        return False
    logger.info("All dependencies OK")
    return True


def _start_thread(name: str, target) -> threading.Thread:
    t = threading.Thread(target=target, name=name, daemon=True)
    t.start()
    logger.info("%s thread started", name)
    return t


def _run_downloader():
    from downloader import PaperDownloader
    PaperDownloader().run()


def _run_slicer():
    from slicer import run_slicer
    run_slicer()


def _run_sorter():
    from sorter import run_sorter
    run_sorter()


def run(workers: list[str]):
    print(HEADER)
    logger.info("Workers: %s", ", ".join(workers))
    logger.info("PDFs:    %s", config.PDF_DIR)
    logger.info("Raw Qs:  %s", config.RAW_QUESTIONS_DIR)
    logger.info("Sorted:  %s", config.SORTED_QUESTIONS_DIR)

    threads: dict[str, threading.Thread] = {}

    if "downloader" in workers:
        threads["downloader"] = _start_thread("downloader", _run_downloader)
        time.sleep(1)

    if "slicer" in workers:
        threads["slicer"] = _start_thread("slicer", _run_slicer)
        time.sleep(1)

    if "sorter" in workers:
        # Sorter has a GUI. Run it in the main thread so Tk is happy,
        # but only after the background workers are spun up.
        _run_sorter()
    else:
        try:
            while any(t.is_alive() for t in threads.values()):
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted... shutting down")

    logger.info("All workers finished")


def main():
    if not _check_dependencies():
        sys.exit(1)

    print(HEADER)
    print(MENU)
    choice = input("  Choice: ").strip()

    mapping = {
        "1": ["downloader", "slicer", "sorter"],
        "2": ["downloader"],
        "3": ["slicer"],
        "4": ["sorter"],
        "5": ["slicer", "sorter"],
    }

    if choice == "0":
        sys.exit(0)
    elif choice in mapping:
        run(mapping[choice])
    else:
        logger.error("Invalid choice: %s", choice)
        sys.exit(1)


if __name__ == "__main__":
    main()