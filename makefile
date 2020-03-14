BDEST := CSViewer
DIST := ./dist
BIN := ./build
BSPEC := CSViewer.spec
BFLAGS := \
	--clean \
	--noconfirm \
	--onefile \
	--windowed \
	--name $(BDEST) \
	--distpath $(DIST) \
	--workpath $(BIN)

VENV := ./venv
PYTHON := $(VENV)/bin/python3
MAIN := CSViewer.py

.PHONY: clean run build exec gen init
default: run

init:
	# refrences global python3.X installation
	python3 -m venv $(VENV); \
	source "$(VENV)/bin/activate"; \
	$(VENV)/bin/pip install --upgrade pip; \
	$(VENV)/bin/pip install -r requirements.txt;

clean:
	rm -rf $(BIN) \
	rm -rf $(DIST)

build:
	source "$(VENV)/bin/activate"; \
	pyinstaller $(BFLAGS) $(BSPEC)

exec:
	$(DIST)/$(BDEST)

run:
	source "$(VENV)/bin/activate"; \
	$(PYTHON) $(MAIN)

gen:
	source "$(VENV)/bin/activate"; \
	pip freeze > requirements.txt
