PY = .venv/bin/python
PELICAN = .venv/bin/pelican

.PHONY: setup build search check serve clean publish

setup:            ## create the venv, install the pinned toolchain, enable the pre-commit hook
	python3 -m venv .venv
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet -r requirements.txt
	git config core.hooksPath .githooks

build:            ## build the site into output/ with local settings, then the search index
	$(PELICAN) content -o output -s pelicanconf.py --fatal errors
	$(PY) -m pagefind --site output --quiet

publish:          ## build with production settings (what the workflow runs)
	$(PELICAN) content -o output -s publishconf.py --fatal warnings

search:           ## build the search index over output/
	$(PY) -m pagefind --site output --quiet

indexnow:         ## tell Bing, Yandex and the rest which pages exist (after a deploy)
	$(PY) tools/indexnow.py

check:            ## PII gate over the tree and the built site, the redirect stubs, the links, and the frames against the CSP
	$(PY) tools/pii_gate.py --tree
	$(PY) tools/pii_gate.py --output output
	$(PY) tools/check_stubs.py output
	$(PY) tools/check_links.py output
	$(PY) tools/check_csp.py output

serve: build search   ## build, index and serve at http://127.0.0.1:8000
	$(PY) tools/serve.py 8000

clean:
	rm -rf output
