GIT		:= git
REPO_URL	:= $(shell $(GIT) config remote.origin.url)
COMMIT		:= $(shell $(GIT) rev-parse HEAD)

nothing:

gh-pages:
	$(MAKE) -C docs clean html
	sed s/_static/static/g -i docs/_build/html/*.html
	mv docs/_build/html/_static docs/_build/html/static
	cd docs/_build/html && $(GIT) init
	cd docs/_build/html && $(GIT) add .
	cd docs/_build/html && $(GIT) commit -m "$(COMMIT)"
	cd docs/_build/html && $(GIT) push -f $(REPO_URL) master:gh-pages
	rm -rf docs/_build/html/.git

.PHONY: nothing gh-pages
