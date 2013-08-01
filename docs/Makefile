SPHINXBUILD	:= sphinx-build
SPHINXOPTS	:=
BUILDDIR	:= _build

html:
	@ mkdir -p $(BUILDDIR)
	$(SPHINXBUILD) -b html -d $(BUILDDIR)/doctrees $(SPHINXOPTS) . $(BUILDDIR)/html

clean:
	- rm -rf $(BUILDDIR)

.PHONY: html clean
