# English project report

**Software-Semantic-Aware Hardware Performance Monitoring** — Liu Qinruo.

- [Compiled PDF](SSA-HPM-report.pdf)
- [Editable LaTeX source](source/main.tex)
- [Complete Overleaf source ZIP](SSA-HPM-overleaf.zip)
- [Source/template provenance](source/third_party/README.md)
- [Measurement inputs](source/data/measurements.json)

The report follows the actual supplied ACL preprint template: A4, 11-point two-column Times-family text, a wide title/author block and author-year BibTeX references. Original template body text, example figures, slides, author fields and student identifiers were excluded. The only report author is Liu Qinruo. Its implementation baseline is the unchanged v0.2.0 release; later presentation commits add the English documentation and report.

Regenerate tables from the committed evidence with `python3 report/generate_tables.py`. Build and package from the repository root:

```sh
python3 report/build.py
```

The helper uses an installed Tectonic or latexmk, builds in a temporary directory and packages only the editable source files. Tectonic 0.17.0 produced the checked PDF. The ZIP has main.tex at its root and can be uploaded directly to Overleaf; use XeLaTeX (or pdfLaTeX), with BibTeX. All figures are editable TikZ/PGFPlots and all measurement tables have accompanying data. No simulation or external design PDF is needed to rebuild the report.
