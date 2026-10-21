# Partner-specific requirement divergence in X12 214 guides

Study for the course Research Methods and Tools, Astana IT University, group SE-2405. Team: Nurassyl Orazbek, Anuar Zhenissov.

Research question: how consistently can a shared, evidence-linked classification scheme identify and categorize partner-specific requirement differences across comparable ANSI X12 214 (004010) truckload implementation guides?

The repository started as a copy of [nurashi/EDI-identifier](https://github.com/nurashi/EDI-identifier) at commit 5e9de2b and keeps its history.

## Contents

| Path | What |
|---|---|
| `schema/` | JSON schemas for a normalized guide and for one judgement on an aligned pair |
| `docs/schema.md` | How guides are normalized |
| `corpus/214-004010/guides/` | Three truckload 214/004010 guides (C.H. Robinson, KBX, Domtar), 118 requirements with page-cited excerpts |
| `corpus/214-004010/annotation/sheet.csv` | 188 annotation units: aligned pair x category |
| `docs/codebook.md` | Labelling rules |
| `backend/cmd/study` | `evidence`, `align`, `sheet`, `agree` |

## Reproduce

The commands are in [`corpus/214-004010/README.md`](corpus/214-004010/README.md). CI runs them on every push: the `pilot` job downloads the PDFs from their public URLs, checks hashes, page counts and every excerpt, aligns the guides and fails if the committed sheet differs from a regenerated one.

## Annotation

Each coder labels a copy of `sheet.csv` named after them, following `docs/codebook.md`, without seeing the other sheet. Round 1 is C.H. Robinson ~ KBX, units U001–U072. Agreement:

```sh
./study agree -disagreements disagreements.csv corpus/214-004010/annotation/<coder-a>.csv corpus/214-004010/annotation/<coder-b>.csv
```
