MAIN     = thesis
LATEX    = pdflatex
BIBER    = biber
GLOSSARY = makeglossaries

.PHONY: all clean distclean check-em-dashes lint

all:
	$(LATEX) -shell-escape $(MAIN)
	$(BIBER)  $(MAIN)
	$(GLOSSARY) $(MAIN)
	$(LATEX) -shell-escape $(MAIN)
	$(LATEX) -shell-escape $(MAIN)

clean:
	rm -f *.aux *.bbl *.bcf *.blg *.glg *.glo *.gls *.ist \
	      *.lof *.log *.lot *.out *.run.xml *.toc *.acn *.acr \
	      *.alg chapters/*.aux frontmatter/*.aux

distclean: clean
	rm -f $(MAIN).pdf

check-em-dashes:
	python3 scripts/check_no_em_dashes_thesis.py

lint: check-em-dashes
