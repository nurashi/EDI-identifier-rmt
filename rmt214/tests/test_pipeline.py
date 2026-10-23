"""Software tests. The tiny records below are hand-made test fixtures used only
to check that the code behaves as specified; they are NOT research data."""

import sys
from pathlib import Path

import pandas as pd
import pytest
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agreement  # noqa: E402
from align import units_for_pairs  # noqa: E402
from prelabel import prelabel  # noqa: E402


def test_kappa_matches_sklearn():
    a = ["NONE", "NONE", "DIFFERENT", "UNKNOWN", "DIFFERENT", "NONE", "UNKNOWN", "DIFFERENT"]
    b = ["NONE", "DIFFERENT", "DIFFERENT", "UNKNOWN", "DIFFERENT", "NONE", "NONE", "DIFFERENT"]
    assert agreement.cohen_kappa(a, b) == pytest.approx(cohen_kappa_score(a, b))


def test_perfect_and_chance_agreement():
    a = ["Y", "N", "Y", "N"]
    assert agreement.cohen_kappa(a, a) == pytest.approx(1.0)
    assert agreement.gwet_ac1(a, a) == pytest.approx(1.0)
    # coder 2 always says the opposite: kappa below zero
    assert agreement.cohen_kappa(a, ["N", "Y", "N", "Y"]) < 0


def rec(guide, seg, elem, att, val, page=1):
    return dict(guide=guide, area="Heading", pos="020", seg_id=seg, elem_ref=elem,
                attribute=att, value=val, page=page, raw=f"{seg}{elem} {att}={val}")


def test_alignment_and_absence_rule():
    c = pd.DataFrame([
        rec("G1", "B10", "B1001", "usage", "Must use"), rec("G2", "B10", "B1001", "usage", "Mandatory"),
        rec("G1", "B10", "B1003", "usage", "Must use"), rec("G2", "B10", "B1003", "usage", "Used"),
        rec("G1", "B10", "B1002", "usage", "Used"),                        # absent in G2
        rec("G1", "AT7", "AT701", "codes", "X1|X3|AF"), rec("G2", "AT7", "AT701", "codes", "X1|AF"),
    ])
    u = prelabel(units_for_pairs(c)).set_index("x12_position")
    assert u.loc["H020 B10 / B1001", "cand_status"] == "NONE"        # Must use == Mandatory
    assert u.loc["H020 B10 / B1003", "cand_status"] == "DIFFERENT"
    assert bool(u.loc["H020 B10 / B1003", "cand_USAGE"])
    assert u.loc["H020 B10 / B1002", "cand_status"] == "UNKNOWN"     # absence != not used
    assert bool(u.loc["H020 AT7 / AT701", "cand_CODES"])
