"""
This is the generic or base sorter worker
For all my OOP bros this is like an interface or abstract class

This was completely coded with AI cuz I hate GUIs and visual stuff. If somebody with acc experience can do this better plez do.
"""

import os
import json
import shutil
import logging
from pathlib import Path

import tkinter as tk
from PIL import Image, ImageTk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import config
from sources import get_source, resolve_source_config

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(config.DATA_DIR, "questions_db.json")

# =============================================================================
# Visual constants
# =============================================================================
BG        = "#0f1117"
SURFACE   = "#1a1d27"
BORDER    = "#2a2d3a"
ACCENT    = "#6c63ff"
TEXT      = "#e8eaf0"
TEXT_DIM  = "#6b7280"
SUCCESS   = "#22c55e"

FONT_MONO  = ("Consolas", 10)         if os.name == "nt" else ("JetBrains Mono", 10)
FONT_BODY  = ("Segoe UI", 10)         if os.name == "nt" else ("SF Pro Display", 10)
FONT_TITLE = ("Segoe UI", 13, "bold") if os.name == "nt" else ("SF Pro Display", 13, "bold")


# =============================================================================
# Path resolution
# =============================================================================

def _resolve_image_path(stored_path: str) -> str:
    """
    Return a usable absolute path for stored_path.

    The DB may contain stale absolute paths from a different machine or
    working directory.  We prefer a path that actually exists; if the stored
    path is broken we fall back to the same filename in RAW_QUESTIONS_DIR.
    """
    if stored_path and os.path.exists(stored_path):
        return stored_path
    if stored_path:
        candidate = os.path.join(config.RAW_QUESTIONS_DIR, os.path.basename(stored_path))
        if os.path.exists(candidate):
            return candidate
    return stored_path   # caller will handle the missing-file error


# =============================================================================
# Main UI
# =============================================================================

class QuestionSorterUI:

    def __init__(self, root: tk.Tk, subjects: dict):
        """
        Parameters
        ----------
        root     : Tk root window
        subjects : The SUBJECTS dict from the active source config.
        """
        self.root     = root
        self.subjects = subjects

        self.root.title("TopicalForge | Question Sorter")
        self.root.configure(bg=BG)
        self.root.geometry("1280x820")
        self.root.minsize(900, 650)

        self.question_queue: list[dict] = []
        self.current_index              = 0
        self._photo                     = None   # prevent GC

        first_subject = next(iter(subjects))
        self.subject_var = tk.StringVar(value=first_subject)

        self._load_questions()
        self._build_ui()
        self._setup_shortcuts()
        self._load_question()

    # =========================================================================
    # Database
    # =========================================================================

    def _load_questions(self):
        """Append any not-yet-tagged QP questions from the DB to the queue."""
        if not os.path.exists(DB_PATH):
            logger.warning("No question database found at %s", DB_PATH)
            return

        with open(DB_PATH) as f:
            db = json.load(f)

        existing_ids = {q["id"] for q in self.question_queue}
        added = 0

        for pdf_name, pdf_data in db.items():
            if "_qp_" not in pdf_name:
                continue
            for q in pdf_data.get("questions", []):
                qid = q.get("id")
                if q.get("topic") is None and qid not in existing_ids:
                    existing_ids.add(qid)
                    self.question_queue.append(q)
                    added += 1

        if added:
            logger.info(
                "Loaded %d untagged questions (total in queue: %d)",
                added,
                len(self.question_queue),
            )

    def _save_topic(self, question: dict, topic: str):
        try:
            with open(DB_PATH) as f:
                db = json.load(f)
            for pdf_data in db.values():
                for q in pdf_data.get("questions", []):
                    if q.get("id") == question["id"]:
                        q["topic"] = topic
            with open(DB_PATH, "w") as f:
                json.dump(db, f, indent=2)
        except Exception as exc:
            logger.error("Failed to save topic: %s", exc)

    # =========================================================================
    # UI construction
    # =========================================================================

    def _build_ui(self):
        # Header bar
        header = tk.Frame(self.root, bg=SURFACE, height=52)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="TopicalForge  |  Question Sorter",
            font=FONT_TITLE,
            bg=SURFACE,
            fg=TEXT,
        ).pack(side=tk.LEFT, padx=20, pady=14)

        self.progress_label = tk.Label(
            header, text="", font=FONT_BODY, bg=SURFACE, fg=TEXT_DIM
        )
        self.progress_label.pack(side=tk.RIGHT, padx=20)

        # Badge shows whether the current question has a mark scheme
        self.ms_badge = tk.Label(header, text="", font=FONT_BODY, bg=SURFACE, fg=SUCCESS)
        self.ms_badge.pack(side=tk.RIGHT, padx=4)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill=tk.X)

        # Meta bar (subject, session, paper, question number)
        self.meta_label = tk.Label(
            self.root,
            text="",
            font=FONT_MONO,
            bg=BG,
            fg=TEXT_DIM,
            anchor="w",
            padx=20,
            pady=6,
        )
        self.meta_label.pack(fill=tk.X)

        # Main split: image viewer (left) + topic panel (right)
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True)

        # --- Image viewer ---------------------------------------------------
        image_frame = tk.Frame(main, bg=SURFACE)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 8), pady=12)

        self.canvas = tk.Canvas(image_frame, bg=SURFACE, highlightthickness=0)
        v_scroll    = tk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._img_container = self.canvas.create_image(0, 0, anchor="nw")

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>",   self._on_mousewheel)
        self.canvas.bind("<Button-5>",   self._on_mousewheel)

        # --- Topic panel (fixed width) --------------------------------------
        panel = tk.Frame(main, bg=SURFACE, width=280)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 16), pady=12)
        panel.pack_propagate(False)

        # Subject selector
        subj_frame = tk.Frame(panel, bg=SURFACE)
        subj_frame.pack(fill=tk.X, padx=12, pady=(14, 0))
        tk.Label(
            subj_frame,
            text="SUBJECT",
            font=(FONT_BODY[0], 9, "bold"),
            bg=SURFACE,
            fg=TEXT_DIM,
        ).pack(anchor="w")

        for code, info in self.subjects.items():
            tk.Radiobutton(
                subj_frame,
                text=info["label"],
                variable=self.subject_var,
                value=code,
                font=FONT_BODY,
                bg=SURFACE,
                fg=TEXT,
                activebackground=SURFACE,
                activeforeground=ACCENT,
                selectcolor=BG,
                indicatoron=True,
                command=self._rebuild_topic_buttons,
            ).pack(anchor="w", pady=1)

        tk.Frame(panel, bg=BORDER, height=1).pack(fill=tk.X, padx=12, pady=10)
        tk.Label(
            panel,
            text="ASSIGN TOPIC",
            font=(FONT_BODY[0], 9, "bold"),
            bg=SURFACE,
            fg=TEXT_DIM,
            padx=12,
        ).pack(anchor="w")

        # Scrollable topic button list
        topics_outer = tk.Frame(panel, bg=SURFACE)
        topics_outer.pack(fill=tk.BOTH, expand=True, pady=4)

        self._topics_canvas = tk.Canvas(topics_outer, bg=SURFACE, highlightthickness=0)
        topics_scroll = tk.Scrollbar(
            topics_outer, orient=tk.VERTICAL, command=self._topics_canvas.yview
        )
        self._topics_canvas.configure(yscrollcommand=topics_scroll.set)
        topics_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._topics_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._topics_inner = tk.Frame(self._topics_canvas, bg=SURFACE)
        self._topics_canvas.create_window((0, 0), window=self._topics_inner, anchor="nw")
        self._topics_inner.bind(
            "<Configure>",
            lambda e: self._topics_canvas.configure(
                scrollregion=self._topics_canvas.bbox("all")
            ),
        )
        self._topics_canvas.bind("<MouseWheel>", self._on_topics_scroll)
        self._topics_canvas.bind("<Button-4>",   self._on_topics_scroll)
        self._topics_canvas.bind("<Button-5>",   self._on_topics_scroll)

        # Navigation buttons at the bottom of the panel
        nav = tk.Frame(panel, bg=SURFACE)
        nav.pack(fill=tk.X, padx=12, pady=(0, 12))
        for btn_text, cmd in [("< Prev", self._prev), ("Skip >", self._skip)]:
            tk.Button(
                nav,
                text=btn_text,
                command=cmd,
                font=FONT_BODY,
                bd=0,
                bg=BORDER,
                fg=TEXT,
                activebackground=ACCENT,
                activeforeground="white",
                padx=8,
                pady=5,
                cursor="hand2",
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self._rebuild_topic_buttons()

    def _rebuild_topic_buttons(self):
        """Destroy and recreate topic buttons for the currently selected subject."""
        for w in self._topics_inner.winfo_children():
            w.destroy()

        code   = self.subject_var.get()
        topics = self.subjects.get(code, {}).get("topics", [])

        for topic in topics:
            btn = tk.Button(
                self._topics_inner,
                text=topic,
                command=lambda t=topic: self._assign(t),
                font=FONT_BODY,
                bd=0,
                bg=BG,
                fg=TEXT,
                activebackground=ACCENT,
                activeforeground="white",
                anchor="w",
                padx=12,
                pady=6,
                cursor="hand2",
            )
            btn.pack(fill=tk.X, padx=8, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=ACCENT))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=BG))

        self._topics_canvas.update_idletasks()
        self._topics_canvas.configure(scrollregion=self._topics_canvas.bbox("all"))

    # =========================================================================
    # Scrolling
    # =========================================================================

    def _on_mousewheel(self, event):
        delta = -1 if (event.num == 4 or event.delta > 0) else 1
        self.canvas.yview_scroll(delta, "units")

    def _on_topics_scroll(self, event):
        delta = -1 if (event.num == 4 or event.delta > 0) else 1
        self._topics_canvas.yview_scroll(delta, "units")

    # =========================================================================
    # Question display
    # =========================================================================

    def _load_question(self):
        if self.current_index >= len(self.question_queue):
            self._show_done()
            return

        q     = self.question_queue[self.current_index]
        total = len(self.question_queue)
        n     = self.current_index + 1

        self.progress_label.config(text=f"{n} / {total}  ({int(n / total * 100)}%)")

        subj_label = self.subjects.get(q["subject_code"], {}).get("label", q["subject_code"])
        has_ms     = bool(q.get("ms_image_path"))
        self.ms_badge.config(text="MS" if has_ms else "")
        self.meta_label.config(
            text=(
                f"{subj_label}   *   {q['session'].upper()}   *   "
                f"Paper {q['paper_num']}   *   Q{q['question_num']}"
            )
        )

        # Switch subject selector to match the question being shown.
        if q["subject_code"] in self.subjects:
            self.subject_var.set(q["subject_code"])
            self._rebuild_topic_buttons()

        # Load and display the question image.
        img_path = _resolve_image_path(q.get("image_path", ""))
        try:
            img = Image.open(img_path)
            self.root.update_idletasks()
            canvas_w = self.canvas.winfo_width() or 800
            if img.width > canvas_w:
                ratio = canvas_w / img.width
                img   = img.resize(
                    (canvas_w, int(img.height * ratio)),
                    Image.Resampling.LANCZOS,
                )
            self._photo = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self._img_container, image=self._photo)
            self.canvas.configure(scrollregion=(0, 0, img.width, img.height))
            self.canvas.yview_moveto(0)
        except Exception as exc:
            logger.error("Failed to load image %s: %s", img_path, exc)
            self.meta_label.config(
                text=f"Image not found: {os.path.basename(img_path or '')}"
            )

    def _show_done(self):
        self.progress_label.config(text="All done")
        self.meta_label.config(text="All questions tagged -- you can close this window.")
        self.canvas.delete("all")
        self.canvas.create_text(
            400, 200,
            text="All questions sorted!",
            fill=SUCCESS,
            font=(FONT_TITLE[0], 20, "bold"),
        )

    # =========================================================================
    # Actions
    # =========================================================================

    def _assign(self, topic: str):
        if self.current_index >= len(self.question_queue):
            return
        q = self.question_queue[self.current_index]
        q["topic"] = topic
        self._save_topic(q, topic)
        self._bundle_to_sorted(q, topic)
        logger.info("Assigned '%s' -> %s", topic, q["id"])
        self.current_index += 1
        self._load_question()

    def _skip(self):
        self.current_index += 1
        self._load_question()

    def _prev(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._load_question()

    def _bundle_to_sorted(self, q: dict, topic: str):
        """
        Copy the QP image (and MS image if available) into:
            sorted_questions/<topic>/<question_id>/qp_<question_id>.png
            sorted_questions/<topic>/<question_id>/ms_<question_id>.png
        """
        q_id     = q["id"]
        dest_dir = os.path.join(config.SORTED_QUESTIONS_DIR, topic, q_id)
        os.makedirs(dest_dir, exist_ok=True)

        qp_src = _resolve_image_path(q.get("image_path", ""))
        if qp_src and os.path.exists(qp_src):
            try:
                shutil.copy2(qp_src, os.path.join(dest_dir, f"qp_{q_id}.png"))
            except Exception as exc:
                logger.error("Failed to copy QP image: %s", exc)
        else:
            logger.warning("QP image missing for %s", q_id)

        ms_src = _resolve_image_path(q.get("ms_image_path") or "")
        if ms_src and os.path.exists(ms_src):
            try:
                shutil.copy2(ms_src, os.path.join(dest_dir, f"ms_{q_id}.png"))
                logger.info("Bundled MS image for %s", q_id)
            except Exception as exc:
                logger.error("Failed to copy MS image: %s", exc)

    # =========================================================================
    # Keyboard shortcuts
    # =========================================================================

    def _setup_shortcuts(self):
        self.root.bind("<Left>",  lambda _: self._prev())
        self.root.bind("<Right>", lambda _: self._skip())
        self.root.bind("<space>", lambda _: self._skip())
        for i in range(1, 10):
            self.root.bind(str(i), lambda _, idx=i - 1: self._quick_assign(idx))

    def _quick_assign(self, idx: int):
        topics = self.subjects.get(self.subject_var.get(), {}).get("topics", [])
        if idx < len(topics):
            self._assign(topics[idx])


# =============================================================================
# Watchdog (reloads questions when new PNGs appear)
# =============================================================================

class _QuestionWatcher(FileSystemEventHandler):
    def __init__(self, ui: QuestionSorterUI):
        self._ui = ui

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".png"):
            logger.info("New image detected: %s", os.path.basename(event.src_path))
            self._ui._load_questions()


# =============================================================================
# Entry point
# =============================================================================

def run_sorter(source_key: str):
    """
    Launch the sorter UI for the given source.

    Parameters
    ----------
    source_key : str
        Key into the source registry, e.g. "bestexamhelp_cie".
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [SORTER] - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(config.LOGS_DIR, "sorter.log")),
            logging.StreamHandler(),
        ],
    )

    entry      = get_source(source_key)
    source_cfg = resolve_source_config(entry["config"])
    subjects   = source_cfg["SUBJECTS"]

    logger.info("Sorter started -- source: %s", entry["label"])

    root = tk.Tk()
    app  = QuestionSorterUI(root, subjects)

    handler  = _QuestionWatcher(app)
    observer = Observer()
    observer.schedule(handler, config.RAW_QUESTIONS_DIR, recursive=False)
    observer.start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Sorter interrupted")
    finally:
        observer.stop()
        observer.join()

    logger.info("Sorter stopped")
