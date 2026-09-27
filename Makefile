PY = .venv/bin/python
PELICAN = .venv/bin/pelican

.PHONY: setup build search check serve clean publish edge links

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

check:            ## PII gate over the tree and the built site, the redirect stubs, the links, the frames against the CSP, and the share tags
	$(PY) tools/pii_gate.py --tree
	$(PY) tools/pii_gate.py --output output
	$(PY) tools/check_stubs.py output
	$(PY) tools/check_links.py output
	$(PY) tools/check_csp.py output
	$(PY) tools/check_meta.py output

edge:             ## check that GitHub Pages and Cloudflare serve the pushed commit (no purge; docs/adr/0010)
	$(PY) tools/purge_edge.py --commit $$(git rev-parse origin/main) --check

links:            ## check the external links of the Portfolio and the main pages (what the monthly workflow runs)
	$(PY) tools/check_external_links.py output

serve: build search   ## build, index and serve at http://127.0.0.1:8000
	$(PY) tools/serve.py 8000

degrade: build search   ## serve at http://127.0.0.1:8001 with every static file off, to see how the pages degrade
	$(PY) tools/serve.py 8001 --html-only

clean:
	rm -rf output
