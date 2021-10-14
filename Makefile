# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

test:
	pip install -e . && cd tests && python3 ./run_pytests.py

publish_bptk:
	cd scripts && ./publish.sh

publish_without_test:
	cd scripts && ./publish_without_test.sh

publish_docker:
	python3 ./build_docker.py

publish_docu:
	cd scripts && ./push_docs_s3.sh && ./invalidate_cloudfront_cache.sh

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
