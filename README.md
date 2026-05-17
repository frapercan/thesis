# Thesis

LaTeX sources for the doctoral thesis of Francisco Miguel Pérez Canales
(PROTEA, Protein functional Embedding-based Annotation).

Co-supervisors: David Orellana-Martín and Ana M. Rojas.

## Layout

- `thesis.tex`: root document.
- `frontmatter/`: title page, abstract, acronyms, glossary entries.
- `chapters/`: body chapters and appendices.
- `figures/`: TikZ sources, generated CSV data, and figure helpers.
- `bibliography/references.bib`: BibLaTeX database.
- `scripts/`: lint helpers (no-em-dash check, bootstrap data).
- `.github/workflows/build.yml`: CI build job.

## Build

The compiled `thesis.pdf` is intentionally not tracked in version
control (see `.gitignore`). To regenerate it locally run:

    latexmk -pdf -shell-escape -interaction=nonstopmode thesis.tex

Equivalent shortcuts:

    make all         # multi-pass pdflatex + biber + makeglossaries
    bash publish.sh  # compile and archive a versioned copy under versions/

The CI workflow `.github/workflows/build.yml` rebuilds the PDF on every
push and pull request to `main` or `develop`, and uploads it as the
`thesis-pdf` artefact (30-day retention).

## Lint

    make lint        # runs scripts/check_no_em_dashes_thesis.py

The lint forbids em-dashes (`--`, U+2014) in thesis prose. Use point,
comma, or parentheses instead.
