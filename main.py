#!/usr/bin/env python3
"""
ts js handles the menus and shi
you can choose what u wanna do and then it'll call all the right workers
"""

import os
import sys
import time
import logging
import threading

import config
import sources   # noqa: F401 -- don't remove ts it is needed for list_sources() in the menu
from sources import list_sources

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
+-------------------------------------------------------+
TopicalForge
+-------------------------------------------------------+
"""


# =============================================================================
# Dependency check
# =============================================================================

def _check_dependencies() -> bool:
    logger.info("Checking dependencies...")
    missing = []
    for mod, pkg in [
        ("selenium", "selenium"),
        ("PIL",      "Pillow"),
        ("fitz",     "PyMuPDF"),
        ("watchdog", "watchdog"),
    ]:
        try:
            __import__("PIL" if mod == "PIL" else mod)
        except ImportError:
            missing.append(pkg)

    if missing:
        logger.error(
            "Missing packages: %s  ->  pip install %s",
            ", ".join(missing),
            " ".join(missing),
        )
        return False

    logger.info("All dependencies OK")
    return True


# =============================================================================
# Worker launchers (called from threads or directly)
# =============================================================================

def _run_downloader(source_key: str):
    from workers.downloader import run_downloader
    run_downloader(source_key)


def _run_slicer(source_key: str):
    from workers.slicer import run_slicer
    run_slicer(source_key)


def _run_sorter(source_key: str):
    from workers.sorter import run_sorter
    run_sorter(source_key)


def _start_thread(name: str, target, source_key: str) -> threading.Thread:
    t = threading.Thread(
        target=target,
        args=(source_key,),
        name=name,
        daemon=True,
    )
    t.start()
    logger.info("%s thread started", name)
    return t


# =============================================================================
# Pipeline runner
# =============================================================================

def run(workers: list[str], source_key: str):
    print(HEADER)
    logger.info("Source:  %s", source_key)
    logger.info("Workers: %s", ", ".join(workers))
    logger.info("PDFs:    %s", config.PDF_DIR)
    logger.info("Raw Qs:  %s", config.RAW_QUESTIONS_DIR)
    logger.info("Sorted:  %s", config.SORTED_QUESTIONS_DIR)

    threads: dict[str, threading.Thread] = {}

    if "downloader" in workers:
        threads["downloader"] = _start_thread("downloader", _run_downloader, source_key)
        time.sleep(1)

    if "slicer" in workers:
        threads["slicer"] = _start_thread("slicer", _run_slicer, source_key)
        time.sleep(1)

    if "sorter" in workers:
        # Tk needa run on the main thread, so we call directly after background
        _run_sorter(source_key)
    else:
        try:
            while any(t.is_alive() for t in threads.values()):
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted -- shutting down")

    logger.info("All workers finished")


# =============================================================================
# Menus
# =============================================================================

def _source_menu() -> str:
    """Show the source selection menu and return the chosen source key."""
    available = list_sources()   # ts wil return a list of (key, label) tuples

    print(HEADER)
    print("  Select a source:\n")
    for i, (key, label) in enumerate(available, start=1):
        print(f"  {i}  {label}")
    print("  0  Exit\n")

    while True:
        raw = input("  Choice: ").strip()
        if raw == "0":
            sys.exit(0)
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(available):
                key, label = available[idx]
                logger.info("Selected source: %s (%s)", label, key)
                return key
        except ValueError:
            pass
        print("  Invalid choice, try again.")

# ts like the menu of options and shi
def _worker_menu(source_label: str) -> list[str]:
    """Show the worker selection menu and return the list of worker names."""
    worker_map = {
        "1": (["downloader", "slicer", "sorter"], "Full pipeline (Downloader + Slicer + Sorter)"),
        "2": (["downloader"],                     "Downloader only"),
        "3": (["slicer"],                         "Slicer only"),
        "4": (["sorter"],                         "Sorter only"),
        "5": (["slicer", "sorter"],               "Slicer + Sorter (PDFs already downloaded)"),
    }

    print(f"\n  Source: {source_label}\n")
    for key, (_, desc) in worker_map.items():
        print(f"  {key}  {desc}")
    print("  0  Back\n")

    while True:
        raw = input("  Choice: ").strip()
        if raw == "0":
            return []   # show menu again
        if raw in worker_map:
            workers, desc = worker_map[raw]
            logger.info("Selected workers: %s", desc)
            return workers
        print("  Invalid choice, try again.")


# =============================================================================
# Entry point
# =============================================================================

def main():
    if not _check_dependencies():
        sys.exit(1)

    while True:
        source_key = _source_menu()
        source_label = next(label for key, label in list_sources() if key == source_key)

        workers = _worker_menu(source_label)
        if not workers:
            continue   # pressed 0 so we go back to source menu

        run(workers, source_key)
        break


if __name__ == "__main__":
    main()
