# SSA-HPM report source

Open main.tex as the root document in Overleaf and use XeLaTeX (or pdfLaTeX) with BibTeX. The supplied ACL preprint style controls A4 paper, 11-point two-column Times-family typography, title treatment and author-year citations. Author: Liu Qinruo.

Local build: `tectonic --keep-logs main.tex`, or `latexmk -pdf main.tex`. Required packages are standard TeX Live packages including pgfplots, TikZ, algorithm, algpseudocode and inconsolata. Tectonic 0.17.0 was used for the checked PDF.

The report text, tables, TikZ diagrams, bibliography, plot CSV and input-measurement JSON are editable. Tables/plot use committed evidence values; data/measurements.json includes input SHA-256 identities. No external image file or original design PDF is required. See third_party/README.md for style provenance and licensing.
