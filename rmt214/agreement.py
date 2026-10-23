"""Inter-coder agreement for the two independent coders (Objective 4).

Inputs: two completed coder sheets (xlsx) with the same unit_id set.
Outputs (out/agreement/):
  status_confusion.csv      3x3 confusion matrix for divergence status
  agreement_summary.csv     percent agreement, Cohen's kappa (+ bootstrap 95% CI),
                            Gwet's AC1, n units -- for status and for each category flag
  disagreements.csv         every unit the coders labelled differently, with the
                            evidence of both guides, for adjudication
"""

from __future__ import annotations

import argparse
from collections import Counter

import numpy as np
import pandas as pd

import config


# ---------- coefficients -----------------------------------------------------

def percent_agreement(a, b) -> float:
    a, b = list(a), list(b)
    return sum(x == y for x, y in zip(a, b)) / len(a)


def cohen_kappa(a, b, labels=None) -> float:
    """Cohen (1960) kappa for two coders, nominal labels."""
    a, b = list(a), list(b)
    n = len(a)
    labels = labels or sorted(set(a) | set(b))
    po = percent_agreement(a, b)
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in labels)
    if pe == 1.0:                # both coders used one identical label throughout
        return float("nan")
    return (po - pe) / (1 - pe)


def gwet_ac1(a, b, labels=None) -> float:
    """Gwet (2008) AC1: less sensitive to skewed prevalence than kappa."""
    a, b = list(a), list(b)
    n = len(a)
    labels = labels or sorted(set(a) | set(b))
    q = len(labels)
    if q < 2:
        return float("nan")
    po = percent_agreement(a, b)
    ca, cb = Counter(a), Counter(b)
    pi = {k: (ca[k] + cb[k]) / (2 * n) for k in labels}
    pe = sum(p * (1 - p) for p in pi.values()) / (q - 1)
    return (po - pe) / (1 - pe)


def bootstrap_ci(a, b, stat, n_boot, seed, alpha=0.05):
    """Percentile bootstrap CI, resampling units with replacement."""
    a, b = np.asarray(a, dtype=object), np.asarray(b, dtype=object)
    rng = np.random.default_rng(seed)
    labels = sorted(set(a) | set(b))
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(a), len(a))
        v = stat(a[idx], b[idx], labels)
        if not np.isnan(v):
            vals.append(v)
    if not vals:
        return (float("nan"), float("nan"))
    return (float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2)))


def summarise(name, a, b, labels):
    k = cohen_kappa(a, b, labels)
    lo, hi = bootstrap_ci(a, b, cohen_kappa, config.BOOTSTRAP_RESAMPLES, config.RANDOM_SEED)
    return {
        "variable": name, "n_units": len(a),
        "percent_agreement": round(percent_agreement(a, b), 4),
        "cohen_kappa": round(k, 4), "kappa_ci95_low": round(lo, 4), "kappa_ci95_high": round(hi, 4),
        "gwet_ac1": round(gwet_ac1(a, b, labels), 4),
        "label_counts_coder1": dict(Counter(a)), "label_counts_coder2": dict(Counter(b)),
    }


# ---------- sheet handling -----------------------------------------------------

def load_coder(path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="units")
    df = df.set_index("unit_id")
    df["status"] = df["status"].astype(str).str.strip().str.upper()
    for c in config.CATEGORIES:
        col = f"cat_{c}"
        df[col] = df[col].fillna("").astype(str).str.strip().str.upper().map(
            lambda v: "Y" if v in {"Y", "YES", "1", "TRUE", "X"} else "N")
    return df


def validate(df, who):
    bad = df[~df["status"].isin(config.STATUS)]
    if len(bad):
        raise SystemExit(f"{who}: {len(bad)} units have no valid status, e.g. {list(bad.index[:5])}")


def run(sheet1, sheet2, out_dir):
    c1, c2 = load_coder(sheet1), load_coder(sheet2)
    validate(c1, "coder1"); validate(c2, "coder2")
    common = c1.index.intersection(c2.index)
    if len(common) != len(c1) or len(common) != len(c2):
        raise SystemExit("coder sheets do not contain the same units")
    c1, c2 = c1.loc[common], c2.loc[common]

    rows = [summarise("status", c1["status"], c2["status"], config.STATUS)]
    # category flags are compared on units BOTH coders called DIFFERENT, so a
    # status disagreement is not counted twice
    both_diff = (c1["status"] == "DIFFERENT") & (c2["status"] == "DIFFERENT")
    for c in config.CATEGORIES:
        col = f"cat_{c}"
        if both_diff.sum():
            rows.append(summarise(c, c1.loc[both_diff, col], c2.loc[both_diff, col], ["N", "Y"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_dir / "agreement_summary.csv", index=False)
    pd.crosstab(c1["status"].rename("coder1"), c2["status"].rename("coder2")) \
        .reindex(index=config.STATUS, columns=config.STATUS, fill_value=0) \
        .to_csv(out_dir / "status_confusion.csv")

    flag_cols = [f"cat_{c}" for c in config.CATEGORIES]
    differs = (c1["status"] != c2["status"]) | (c1[flag_cols] != c2[flag_cols]).any(axis=1)
    ev_cols = [c for c in c1.columns if c.startswith(("a_", "b_")) or c in ("x12_position", "guide_pair")]
    dis = c1.loc[differs, ev_cols].copy()
    for who, df in (("coder1", c1), ("coder2", c2)):
        dis[f"{who}_status"] = df.loc[differs, "status"]
        dis[f"{who}_cats"] = df.loc[differs, flag_cols].apply(
            lambda r: ",".join(c[4:] for c in flag_cols if r[c] == "Y"), axis=1)
        dis[f"{who}_note"] = df.loc[differs, "note"] if "note" in df else ""
    dis.to_csv(out_dir / "disagreements.csv")
    return pd.DataFrame(rows), dis


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("coder1"); ap.add_argument("coder2")
    ap.add_argument("--out", default=str(config.OUT_DIR / "agreement"))
    a = ap.parse_args()
    from pathlib import Path
    summary, dis = run(a.coder1, a.coder2, Path(a.out))
    print(summary.to_string(index=False))
    print(f"{len(dis)} units to adjudicate")
