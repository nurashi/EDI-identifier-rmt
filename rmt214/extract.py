"""Stage 1-2: PDF -> page text -> constraint records (Objective 2-3 input).

Text layer is read with poppler `pdftotext -layout`, one page at a time, so every
record keeps the page number and the exact source line as evidence. Pages
without a text layer are listed in the manifest as 'no_text' (scanned pages are
not OCR'd in this pilot -- a recorded limitation).

The parser recognises the common implementation-guide layout (segment header
with Pos/Max/Usage lines, element table 'Ref Id Element Name Req Type Min/Max
Usage', code list under each element). Lines it cannot interpret are written to
out/<guide>_unparsed.txt so extraction coverage can be audited.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pandas as pd

import config

SEG_IDS = ("ST SE B10 L11 MAN K1 N1 N2 N3 N4 G62 MS3 LX AT7 MS1 MS2 Q7 AT5 AT8 CD3 "
           "NM1 SPO SDQ OID H3 L3 MEA MS4 G61 G6 NTE PLD").split()
SEG_RE = re.compile(r"^\s*(" + "|".join(SEG_IDS) + r")\s{1,}([A-Z][A-Za-z/&,'\- ]{3,})\s*$")
POS_RE = re.compile(r"Pos(?:ition)?\s*:?\s*(\d{3,4})", re.I)
MAX_RE = re.compile(r"Max(?:imum)?(?:\s*Use)?\s*:?\s*(>?\s*\d+)", re.I)
AREA_RE = re.compile(r"\b(Heading|Detail|Summary)\b", re.I)
LOOP_RE = re.compile(r"Loop\s*:?\s*([0-9A-Z/]{2,})(?:\s+Repeat\s*:?\s*(>?\s*\d+))?", re.I)
USAGE_RE = re.compile(r"(?:User Option\s*\(Usage\)|Usage)\s*:?\s*(Must use|Used|Not used|Mandatory|Optional|Recommended|Conditional)", re.I)
ELEM_RE = re.compile(
    r"^\s*(?P<ref>[A-Z][A-Z0-9]{1,2}\d{2})\s+(?P<id>\d{1,4})\s+(?P<name>.+?)\s{2,}"
    r"(?P<req>M|O|X)\s+(?P<type>AN|ID|DT|TM|R|N\d?)\s+(?P<min>\d+)\s*/\s*(?P<max>\d+)"
    r"(?:\s+(?P<usage>Must use|Used|Not used|Recommended))?\s*$", re.I)
CODE_HEAD_RE = re.compile(r"(CodeList Summary|Code\s+Name|Code\s+Value|Codes?\s*:)", re.I)
CODE_RE = re.compile(r"^\s{0,12}([A-Z0-9]{1,3})\s{2,}(\S.{2,})$")
NOTE_RE = re.compile(r"^\s*(Notes?|Comments?|Semantics?|Syntax Notes?|Semantic Notes?)\s*:\s*(.+)$", re.I)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pdf_pages(path: Path) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True,
                         text=True, check=True).stdout
    pages = out.split("\f")
    return pages[:-1] if pages and not pages[-1].strip() else pages


def parse_guide(guide: str, pages: list[str]):
    recs, unparsed = [], []
    seg = None          # current segment context
    elem = None         # current element (for codes and notes)
    in_codes = False

    def add(att, val, page, raw, elem_ref=""):
        recs.append(dict(guide=guide, area=seg["area"], pos=seg["pos"], seg_id=seg["seg_id"],
                         elem_ref=elem_ref, attribute=att, value=str(val).strip(),
                         page=page, raw=raw.strip()[:240]))

    for pno, text in enumerate(pages, start=1):
        for line in text.splitlines():
            if not line.strip():
                continue
            m = SEG_RE.match(line)
            if m and "Element" not in line:
                seg = dict(seg_id=m.group(1), name=m.group(2).strip(), area="", pos="", page=pno)
                elem, in_codes = None, False
                continue
            if seg is None:
                continue
            if not seg["pos"] and (pm := POS_RE.search(line)):
                seg["pos"] = pm.group(1).zfill(3)[-3:] if len(pm.group(1)) <= 3 else pm.group(1)
                if mm := MAX_RE.search(line):
                    add("max_use", mm.group(1).replace(" ", ""), pno, line)
            if not seg["area"] and (am := AREA_RE.search(line)) and elem is None:
                seg["area"] = am.group(1).title()
            if lm := LOOP_RE.search(line):
                if lm.group(2):
                    add("loop_repeat", lm.group(2).replace(" ", ""), pno, line)
            if (um := USAGE_RE.search(line)) and elem is None:
                add("usage", um.group(1), pno, line)
                continue
            em = ELEM_RE.match(line)
            if em:
                elem, in_codes = em.group("ref").upper(), False
                add("req", em.group("req").upper(), pno, line, elem)
                add("data_type", em.group("type").upper(), pno, line, elem)
                add("min_len", em.group("min"), pno, line, elem)
                add("max_len", em.group("max"), pno, line, elem)
                if em.group("usage"):
                    add("usage", em.group("usage"), pno, line, elem)
                continue
            if elem and CODE_HEAD_RE.search(line):
                in_codes = True
                continue
            if elem and in_codes and (cm := CODE_RE.match(line)):
                add("_code", cm.group(1), pno, line, elem)
                continue
            if nm := NOTE_RE.match(line):
                add("notes", nm.group(2), pno, line, elem or "")
                continue
            unparsed.append(f"p{pno}: {line.rstrip()}")

    df = pd.DataFrame(recs)
    if df.empty:
        return df, unparsed
    # collapse individual code lines into one sorted code-set record per element
    codes = df[df["attribute"] == "_code"]
    rest = df[df["attribute"] != "_code"]
    grouped = []
    for key, g in codes.groupby(["area", "pos", "seg_id", "elem_ref"], sort=False):
        grouped.append(dict(guide=guide, area=key[0], pos=key[1], seg_id=key[2], elem_ref=key[3],
                            attribute="codes", value="|".join(sorted(set(g["value"]))),
                            page=int(g["page"].min()),
                            raw=f"{len(set(g['value']))} codes listed, pages {sorted(set(g['page']))}"))
    return pd.concat([rest, pd.DataFrame(grouped)], ignore_index=True), unparsed


def run():
    config.OUT_DIR.mkdir(exist_ok=True)
    manifest, frames = {}, []
    for g, meta in config.GUIDES.items():
        p = config.GUIDE_DIR / meta["file"]
        if not p.exists():
            manifest[g] = {"file": meta["file"], "status": "missing"}
            continue
        pages = pdf_pages(p)
        no_text = [i for i, t in enumerate(pages, 1) if len(t.strip()) < 20]
        (config.OUT_DIR / f"{g}_pages.json").write_text(json.dumps(pages))
        df, unparsed = parse_guide(g, pages)
        (config.OUT_DIR / f"{g}_unparsed.txt").write_text("\n".join(unparsed))
        frames.append(df)
        manifest[g] = {"file": meta["file"], "sha256": sha256(p), "pages": len(pages),
                       "pages_without_text": no_text, "records": len(df),
                       "segments": int(df["seg_id"].nunique()) if len(df) else 0,
                       "unparsed_lines": len(unparsed)}
    (config.OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    allc = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    allc.to_csv(config.OUT_DIR / "constraints.csv", index=False)
    return allc, manifest


if __name__ == "__main__":
    c, m = run()
    print(json.dumps(m, indent=2))
