MAIN = PROTEA_campana
LATEX = pdflatex

.PHONY: all clean distclean

all:
	$(LATEX) -interaction=nonstopmode $(MAIN).tex
	$(LATEX) -interaction=nonstopmode $(MAIN).tex

clean:
	rm -f *.aux *.log *.out *.toc *.lof *.lot secciones/*.aux

distclean: clean
	rm -f $(MAIN).pdf
