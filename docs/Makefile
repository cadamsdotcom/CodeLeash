CHAPTERS := $(sort $(wildcard *.md))
BUILDDIR := build

.PHONY: html clean

html: $(BUILDDIR)/index.html $(BUILDDIR)/style.css

$(BUILDDIR)/index.html: $(CHAPTERS) metadata.yaml style.css
	@mkdir -p $(BUILDDIR)
	(for f in $(CHAPTERS); do cat "$$f"; echo; echo; done) | pandoc \
		--from markdown \
		--to html5 \
		--standalone \
		--toc \
		--number-sections \
		--css style.css \
		--metadata-file=metadata.yaml \
		--output $@

$(BUILDDIR)/style.css: style.css
	@mkdir -p $(BUILDDIR)
	cp style.css $(BUILDDIR)/style.css

clean:
	rm -rf $(BUILDDIR)
