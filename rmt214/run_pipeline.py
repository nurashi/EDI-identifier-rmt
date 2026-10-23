"""End-to-end pilot run: extract -> align -> candidate overview -> blind coder sheets.

    python3 run_pipeline.py            # writes everything to out/
    python3 agreement.py out/coder_sheets/coder1.xlsx out/coder_sheets/coder2.xlsx

Every number reported in the Assignment 3 appendix comes from files in out/.
"""

import json
import platform
import sys

import pandas as pd
import pdfplumber
import openpyxl

import config
import extract
from align import units_for_pairs
from annotate import export
from prelabel import prelabel


def versions():
    import subprocess
    pt = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True).stderr.splitlines()[0]
    return {"python": platform.python_version(), "pandas": pd.__version__,
            "openpyxl": openpyxl.__version__, "pdfplumber": pdfplumber.__version__,
            "pdftotext": pt, "seed": config.RANDOM_SEED}


def main():
    constraints, manifest = extract.run()
    if constraints.empty or constraints["guide"].nunique() < 2:
        sys.exit("need at least two guides with extracted records; see out/manifest.json")

    units = prelabel(units_for_pairs(constraints))
    units.to_csv(config.OUT_DIR / "units_with_candidates.csv", index=False)

    # descriptive overview used to check the coding sample covers every category
    ov = units.groupby(["guide_pair", "documented_in"]).size().rename("units").reset_index()
    ov.to_csv(config.OUT_DIR / "overview_documentation.csv", index=False)
    st = units.groupby(["guide_pair", "cand_status"]).size().unstack(fill_value=0)
    st.to_csv(config.OUT_DIR / "overview_candidate_status.csv")
    cat = units[units["cand_status"] == "DIFFERENT"].groupby("guide_pair")[
        [f"cand_{c}" for c in config.CATEGORIES]].sum()
    cat.to_csv(config.OUT_DIR / "overview_candidate_categories.csv")

    sheets = config.OUT_DIR / "coder_sheets"
    sheets.mkdir(exist_ok=True)
    labels = {g: m["label"] for g, m in config.GUIDES.items()}
    blind = units.drop(columns=[c for c in units.columns if c.startswith("cand_")])
    for coder in ("coder1", "coder2"):
        export(blind, sheets / f"{coder}.xlsx", coder, labels)

    (config.OUT_DIR / "run_info.json").write_text(json.dumps(
        {"versions": versions(), "manifest": manifest, "n_units": len(units)}, indent=2))
    print(json.dumps(manifest, indent=2))
    print("\nunits per pair / documentation:\n", ov.to_string(index=False))
    print("\ncandidate status:\n", st.to_string())
    print("\ncandidate categories (DIFFERENT units):\n", cat.to_string())


if __name__ == "__main__":
    main()
