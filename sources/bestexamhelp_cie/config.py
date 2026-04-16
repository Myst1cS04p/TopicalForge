"""
sources/bestexamhelp_cie/config.py

Subject configuration and setting overrides for the BestExamHelp / CIE A-Level
source.  Any key defined here takes priority over the global defaults in the
root config.py.  Keys you omit fall back to the global defaults automatically.

HOW TO ADD A SUBJECT
--------------------
Append a new entry to SUBJECTS following the pattern below.

Required keys per subject:
    name   -- lowercase URL slug used on bestexamhelp.com
               (no spaces, no underscores -- hyphens only)
    label  -- human-readable display name for the UI
    papers -- list of paper number strings to attempt, e.g. ["1", "2", "3"]
    topics -- ordered list of topic strings shown in the Sorter UI
"""

# =============================================================================
# CIE-specific overrides (comment out to inherit the global default)
# =============================================================================
PAPER_TYPES = ["qp", "ms"]
START_YEAR  = 2022
END_YEAR    = 2024
SESSIONS    = ["s", "w"]   # s = summer, w = winter

# Variants to try for each paper number (1, 2, 3 -- i.e. paper 11, 12, 13)
VARIANTS = [1, 2, 3]

# =============================================================================
# Subjects
# =============================================================================
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
            "P3 - Logarithms and Exponentials",
            "P3 - Trigonometry",
            "P3 - Differentiation",
            "P3 - Integration",
            "P3 - Numerical Methods",
            "P3 - Vectors",
            "P3 - Differential Equations",
            "P3 - Complex Numbers",
            "P4 - Forces and Equilibrium",
            "P4 - Kinematics",
            "P4 - Momentum",
            "P4 - Newton's Laws",
            "P4 - Work, Energy and Power",
            "P5 - Representation of Data",
            "P5 - Permutations and Combinations",
            "P5 - Probability",
            "P5 - Discrete Random Variables",
            "P5 - Normal Distribution",
        ],
    },

    # -------------------------------------------------------------------------
    # Uncomment (and fill in topics) to enable additional subjects.
    # -------------------------------------------------------------------------

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
    #         "Cell Membranes and Transport",
    #         "Mitosis",
    #         "Nucleic Acids and Protein Synthesis",
    #         "Transport in Plants",
    #         "Transport in Animals",
    #         "Immunity",
    #         "Genetics",
    #         "Evolution",
    #         "Ecology",
    #     ],
    # },
    # "9618": {
    #     "name": "computer-science",
    #     "label": "Computer Science",
    #     "papers": ["1", "2", "3", "4"],
    #     "topics": [
    #         "Information Representation",
    #         "Communication and Internet",
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
}
