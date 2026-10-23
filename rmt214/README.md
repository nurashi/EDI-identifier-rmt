# Assignment 3 Python pipeline

Source extracted unchanged from [rmt214_pipeline.zip](../assignments/assignment-3/rmt214_pipeline.zip).
See the [supplied report](../assignments/assignment-3/Assignment3_Orazbek_Zhenissov.docx)
for the research design and draft codebook.

## Setup and tests

Requires Python 3.12+ and Poppler (`pdftotext` available on PATH).
On Ubuntu: `sudo apt-get install poppler-utils`.
On Windows: install Poppler and add its `Library/bin` directory to PATH.

From the repository root:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r rmt214/requirements-dev.txt
python -m pytest -v rmt214/tests
```

The four original tests cover PDF extraction through workbook export, usage
normalisation, missing positions and agreement calculations. CI installs the
required dependencies and runs these fixture tests without downloading partner PDFs.

## Run

Place source PDFs in `rmt214/data/guides/` using these filenames:

- `chr-truckload-tl-carrier-x12-214.pdf`
- `KBXTECH214-1.pdf`
- `214SPECS_toolkit.pdf`

Source URLs and revision metadata are in the existing
[corpus guide files](../corpus/214-004010/guides/). Confirm eligibility and revision
against the actual PDFs before coding.

```sh
python rmt214/run_pipeline.py
python rmt214/agreement.py rmt214/out/coder_sheets/coder1.xlsx rmt214/out/coder_sheets/coder2.xlsx
```

Run agreement only after both coders independently complete their sheets.
Generated outputs live in `rmt214/out/`: source manifest, extracted constraints,
aligned units, candidate summaries and blind coder workbooks. Source PDFs and
outputs are excluded from Git. Archive completed sheets before rerunning the
pipeline, which overwrites exports.

## Scope

This is the supplied initial prototype. Candidate labels are not research results;
parser coverage on real guide layouts and the independent coding procedure still
need validation. The report's sampling, calibration and audit steps are not
implemented automatically. Check extracted text for contact details before sharing.

Use this prototype's report/codebook and workbooks together; the existing Go pilot
uses a different annotation format.
