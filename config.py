import os

# ==================================================================
# Subject configurations
#
# To add a new subject, just append a new entry to SUBJECTS.
# Required keys:
#   name     - lowercase slug used in URLs  (e.g. "english-literature") DO NOT USE SPACES OR UNDERSCORES
#   label    - human-readable display name  (e.g. "English Literature")
#   papers   - list of paper numbers to try (e.g. ["1", "2", "3"])
#   topics   - list of topic strings shown in the Sorter UI
# ==================================================================
SUBJECTS = {
    "9709": {
        "name": "mathematics",
        "label": "Mathematics",
        "papers": ["1", "3", "4", "5"],
        "topics": [
            "P1 - Quadratics",
            "P1 - Functions",
            "P1 - Coordinate Geometry",
            "P1 - Circular Measure",
            "P1 - Trigonometry",
            "P1 - Series",
            "P1 - Differentiation",
            "P1 - Integration",
            "P3 - Algebra",
            "P3 - Logarithms & Exponentials",
            "P3 - Trigonometry",
            "P3 - Differentiation",
            "P3 - Integration",
            "P3 - Numerical Methods",
            "P3 - Vectors",
            "P3 - Differential Equations",
            "P3 - Complex Numbers",
            "P4 - Forces & Equilibrium",
            "P4 - Kinematics",
            "P4 - Momentum",
            "P4 - Newton's Laws",
            "P4 - Work, Energy & Power",
            "P5 - Representation of Data",
            "P5 - Permutations & Combinations",
            "P5 - Probability",
            "P5 - Discrete Random Variables",
            "P5 - Normal Distribution",
        ],
    },
    # Add more subjects here as needed, following the same structure. 
    # "9702": {
    #     "name": "physics",
    #     "label": "Physics",
    #     "papers": ["2", "4", "5"],
    #     "topics": [
    #         "Mechanics",
    #         "Electricity",
    #         "Waves",
    #         "Matter",
    #         "Modern Physics",
    #         "Practical Skills",
    #     ],
    # },
    # "9700": {
    #     "name": "biology",
    #     "label": "Biology",
    #     "papers": ["1", "2", "4", "5"],
    #     "topics": [
    #         "Cell Structure",
    #         "Biological Molecules",
    #         "Enzymes",
    #         "Cell Membranes & Transport",
    #         "Mitosis",
    #         "Nucleic Acids & Protein Synthesis",
    #         "Transport in Plants",
    #         "Transport in Animals",
    #         "Immunity",
    #         "Genetics",
    #         "Evolution",
    #         "Ecology",
    #     ],
    # },
    # "9093": {
    #     "name": "english-language",
    #     "label": "English Language",
    #     "papers": ["1", "2", "3", "4"],
    #     "topics": [
    #         "Reading for Meaning",
    #         "Summary Writing",
    #         "Directed Writing",
    #         "Composition",
    #         "Language Analysis",
    #     ],
    # },
    # "9695": {
    #     "name": "english-literature",
    #     "label": "English Literature",
    #     "papers": ["1", "2", "3", "4"],
    #     "topics": [
    #         "Poetry",
    #         "Prose",
    #         "Drama",
    #         "Unseen",
    #         "Coursework",
    #     ],
    # },
    # "9618": {
    #     "name": "computer-science",
    #     "label": "Computer Science",
    #     "papers": ["1", "2", "3", "4"],
    #     "topics": [
    #         "Information Representation",
    #         "Communication & Internet",
    #         "Hardware",
    #         "Software Development",
    #         "System Software",
    #         "Security",
    #         "Artificial Intelligence",
    #         "Databases",
    #         "Data Structures",
    #         "Algorithms",
    #     ],
    # },
}

# ===================
# Download settings
# ===================
PAPER_TYPES = ["qp", "ms"]   # Question Paper and Mark Scheme
START_YEAR  = 2022
END_YEAR    = 2024
SESSIONS    = ["s", "w"]     # s = Summer, w = Winter

# ===================
# Slicer settings
# ===================
# Minimum vertical gap (pts) before a new question block is accepted.
# Raise this if you're getting too many false-positive question splits.
MIN_QUESTION_HEIGHT = 40

# Maximum "reasonable" question number.  Blocks whose detected number exceeds
# this are treated as false positives (e.g. "20 cm", "30 marks" annotations).
MAX_QUESTION_NUMBER = 30

# ===================
# Watchdog / Selenium 
# ===================
# (Don't change these unless you know what you're doing)
WATCH_INTERVAL   = 2
HEADLESS_MODE    = False
DOWNLOAD_TIMEOUT = 30

# ===================
# Directory structure
# ===================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
RAW_QUESTIONS_DIR = os.path.join(DATA_DIR, "raw_questions")
SORTED_QUESTIONS_DIR = os.path.join(DATA_DIR, "sorted_questions")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

for directory in [PDF_DIR, RAW_QUESTIONS_DIR, SORTED_QUESTIONS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)