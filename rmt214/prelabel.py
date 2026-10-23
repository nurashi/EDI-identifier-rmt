"""Rule-based candidate labels for each aligned unit.

These labels are NOT shown to the human coders (to avoid anchoring). They serve
two purposes only: (1) a descriptive overview of where documented values differ,
used to check that the coding sample contains every category, and (2) a simple
reference condition for the later dissertation toolkit, which will be compared
with the adjudicated human labels -- not with the coders' raw labels.
"""

from __future__ import annotations

import re

import pandas as pd

import config

USAGE_NORMAL = {
    "MUST USE": "MUST_USE", "MANDATORY": "MUST_USE", "M": "MUST_USE", "REQUIRED": "MUST_USE",
    "USED": "USED", "OPTIONAL": "USED", "O": "USED", "RECOMMENDED": "USED", "CONDITIONAL": "USED",
    "NOT USED": "NOT_USED", "N/U": "NOT_USED", "NOT USED.": "NOT_USED",
}
COND_WORDS = re.compile(r"\b(if|when|only|unless|required for|must be sent|condition|otherwise)\b", re.I)


def norm_usage(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
        return None
    return USAGE_NORMAL.get(str(v).strip().upper(), str(v).strip().upper())


def norm_codes(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
        return None
    return frozenset(x for x in str(v).split("|") if x)


def candidate(row) -> dict:
    """Return candidate status and category flags for one unit."""
    flags = {c: False for c in config.CATEGORIES}
    if row["documented_in"] != "both":
        return {"cand_status": "UNKNOWN", **{f"cand_{c}": False for c in config.CATEGORIES},
                "cand_reason": f"position documented only in {row['documented_in']}"}
    reasons, missing = [], []
    for att, cat in config.ATTRIBUTE_CATEGORY.items():
        va, vb = row.get(f"{att}__A"), row.get(f"{att}__B")
        na_a = va is None or (isinstance(va, float) and pd.isna(va)) or va == ""
        na_b = vb is None or (isinstance(vb, float) and pd.isna(vb)) or vb == ""
        if att == "notes":
            ca = (not na_a) and bool(COND_WORDS.search(str(va)))
            cb = (not na_b) and bool(COND_WORDS.search(str(vb)))
            if ca or cb:
                flags[cat] = True
                reasons.append("conditional wording in " + ("both" if ca and cb else ("A" if ca else "B")))
            continue
        if na_a and na_b:
            continue
        if na_a or na_b:
            missing.append(att)
            continue
        if att in ("usage", "req"):
            differ = norm_usage(va) != norm_usage(vb)
        elif att == "codes":
            differ = norm_codes(va) != norm_codes(vb)
        else:
            differ = str(va).strip().upper() != str(vb).strip().upper()
        if differ:
            flags[cat] = True
            reasons.append(f"{att}: {va} vs {vb}")
    if any(flags.values()):
        status = "DIFFERENT"
    elif missing:
        status = "UNKNOWN"
        reasons.append("attribute stated in one guide only: " + ",".join(missing))
    else:
        status = "NONE"
    return {"cand_status": status, **{f"cand_{c}": v for c, v in flags.items()},
            "cand_reason": "; ".join(reasons)}


def prelabel(units: pd.DataFrame) -> pd.DataFrame:
    lab = units.apply(candidate, axis=1, result_type="expand")
    return pd.concat([units, lab], axis=1)
