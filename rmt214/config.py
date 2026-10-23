"""Study configuration: guide registry, codebook labels and fixed settings.

Everything that changes the result of a run is defined here so the run can be
reproduced from this file plus the three source PDFs (identified by SHA-256).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
GUIDE_DIR = ROOT / "data" / "guides"      # source PDFs (not redistributed)
OUT_DIR = ROOT / "out"                    # all generated evidence

# Candidate guides named in Assignment 2. Revision/date are checked against the
# document itself during extraction and recorded in out/manifest.json.
GUIDES = {
    "CHR": {"label": "C.H. Robinson Truckload TL Carrier X12-214",
            "file": "chr-truckload-tl-carrier-x12-214.pdf"},
    "KBX": {"label": "KBX Technology Solutions 214 (ASC X12 4010)",
            "file": "KBXTECH214-1.pdf"},
    "DOM": {"label": "Domtar Paper Transportation 214 (ASC X12 4010)",
            "file": "214SPECS_toolkit.pdf"},
}

TRANSACTION = "214"
VERSION = "004010"

# ---- Codebook (operational definitions are in codebook.md) -----------------
# (a) divergence status of one aligned unit, coded once per unit
STATUS = ["NONE", "DIFFERENT", "UNKNOWN"]
# (b) divergence categories, coded as yes/no flags when status == DIFFERENT
CATEGORIES = ["USAGE", "CODES", "REPETITION", "LENGTH_FORMAT", "CONDITION"]

# Attributes the extractor reads from a guide, and the category each feeds.
ATTRIBUTE_CATEGORY = {
    "usage": "USAGE",          # Must use / Used / Not used / Mandatory / Optional
    "req": "USAGE",            # X12 requirement designator M / O / X
    "max_use": "REPETITION",   # segment max use
    "loop_repeat": "REPETITION",
    "min_len": "LENGTH_FORMAT",
    "max_len": "LENGTH_FORMAT",
    "data_type": "LENGTH_FORMAT",
    "codes": "CODES",          # set of permitted code values
    "notes": "CONDITION",      # free-text conditional / semantic instructions
}

RANDOM_SEED = 20261023      # unit order in coder sheets and bootstrap
BOOTSTRAP_RESAMPLES = 2000
