# Assignment 3

Research Methods and Tools, SE-2405. Nurassyl Orazbek and Anuar Zhenissov.

- [Report](Assignment3_Orazbek_Zhenissov.docx) — supplied Word document, unchanged.
- [Original ZIP](rmt214_pipeline.zip) — supplied archive, unchanged.
- [Python pipeline](../../rmt214/README.md) — extracted source, setup and test commands.

The report describes a document-processing prototype for comparing partner-specific
X12 214 / 004010 requirements and preparing independent coder workbooks. The source
and its four original tests are preserved as supplied. Tests use artificial fixtures;
they are not findings from real partner documents or completed human coding.

This Python prototype is separate from the existing Go pilot. It uses one aligned
position with a status and five category flags; the Go pilot uses a pair/category row.
Their annotation files and agreement results are not interchangeable.

Before submission, check the report's environment/test claims and guide revision
dates against the actual run and the existing corpus metadata. Real-guide parser
auditing, calibration, sampling and independent coding remain research steps.
