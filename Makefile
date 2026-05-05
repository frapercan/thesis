MAIN     = thesis
LATEX    = pdflatex
BIBER    = biber
GLOSSARY = makeglossaries

.PHONY: all clean distclean

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
