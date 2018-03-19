# Copyright (c) 2017, Somia Reality Oy
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

PYTHON		?= python3

GIT		:= git
REPO_URL	:= $(shell $(GIT) config remote.origin.url)
COMMIT		:= $(shell $(GIT) rev-parse HEAD)

nothing:

build:
	$(PYTHON) setup.py build

gh-pages: build
	$(MAKE) -C docs clean html
	sed s/_static/static/g -i docs/_build/html/*.html
	mv docs/_build/html/_static docs/_build/html/static
	cd docs/_build/html && $(GIT) init
	cd docs/_build/html && $(GIT) add .
	cd docs/_build/html && $(GIT) commit -m "$(COMMIT)"
	cd docs/_build/html && $(GIT) push -f $(REPO_URL) master:gh-pages
	rm -rf docs/_build/html/.git

clean:
	rm -rf build
	$(MAKE) -C docs clean

.PHONY: nothing build gh-pages clean
