"""Align constraint records of two guides into comparison units (Objective 2-3).

Unit of analysis = one X12 position (a segment, or one element of a segment,
identified by area + position number + segment id [+ element ref]) documented
by at least one guide of a guide pair. Each unit carries every extracted
attribute of both guides with its page number and source line, so a coder can
judge it from the evidence alone.

Absence rule (Assignment 2): a position that a guide does not document is NOT
coded as "not used"; the attribute value is left blank and the evidence column
says "not documented". Only an explicit "Not Used"/"X" statement counts as usage.
"""

from __future__ import annotations

import itertools

import pandas as pd

import config

KEY = ["area", "pos", "seg_id", "elem_ref"]
NOT_DOC = "not documented"


def position_label(r) -> str:
    base = f"{r['area'][:1]}{r['pos']} {r['seg_id']}" if r["pos"] else r["seg_id"]
    return f"{base} / {r['elem_ref']}" if r["elem_ref"] else base


def wide(constraints: pd.DataFrame, guide: str) -> pd.DataFrame:
    """One row per position for one guide: value, page and evidence per attribute."""
    g = constraints[constraints["guide"] == guide]
    rows = {}
    for _, r in g.iterrows():
        k = tuple(r[c] for c in KEY)
        row = rows.setdefault(k, dict(zip(KEY, k)))
        att = r["attribute"]
        if att in row:          # duplicate: keep first, append evidence
            row[f"{att}__ev"] += f" || p{r['page']}: {r['raw']}"
            continue
        row[att] = r["value"]
        row[f"{att}__page"] = r["page"]
        row[f"{att}__ev"] = f"p{r['page']}: {r['raw']}"
    return pd.DataFrame(rows.values())


def align_pair(constraints: pd.DataFrame, ga: str, gb: str) -> pd.DataFrame:
    a, b = wide(constraints, ga), wide(constraints, gb)
    m = a.merge(b, on=KEY, how="outer", suffixes=("__A", "__B"), indicator=True)
    m["guide_pair"] = f"{ga}-{gb}"
    m["documented_in"] = m["_merge"].map({"both": "both", "left_only": ga, "right_only": gb})
    return m.drop(columns="_merge")


def units_for_pairs(constraints: pd.DataFrame) -> pd.DataFrame:
    guides = sorted(constraints["guide"].unique())
    frames = [align_pair(constraints, ga, gb) for ga, gb in itertools.combinations(guides, 2)]
    u = pd.concat(frames, ignore_index=True)
    u["x12_position"] = u.apply(position_label, axis=1)
    u["unit_id"] = [f"U{i:04d}" for i in range(1, len(u) + 1)]
    return u


def attr_cols(units: pd.DataFrame, side: str):
    """Columns for one side ('A' or 'B') in a tidy order for coder sheets."""
    out = []
    for att in config.ATTRIBUTE_CATEGORY:
        for suf in ("", "__page", "__ev"):
            c = f"{att}{suf}__{side}"
            if c in units.columns:
                out.append(c)
    return out
