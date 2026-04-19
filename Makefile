PYTHON ?= /Users/erikh/code/carryall/authority-runtime-python/.venv/bin/python

.PHONY: demo setup clean layer1 layer2 layer3 verify

demo: layer1 pause layer2 pause layer3
	@echo
	@echo "--- end of demo ---"

layer1:
	@bash scripts/01_manifest.sh

layer2:
	@$(PYTHON) scripts/02_baton.py

layer3:
	@CARRYALL_SLOS_CONFIG=./backend.json $(PYTHON) scripts/03_carryall.py

pause:
	@echo
	@read -p "[press enter for next layer]" _ignore

verify:
	@$(PYTHON) scripts/02_baton.py >/dev/null
	@CARRYALL_SLOS_CONFIG=./backend.json $(PYTHON) scripts/03_carryall.py
	@echo "ok"

setup:
	@$(PYTHON) -m pip install -e /Users/erikh/code/carryall/authority-runtime-python
	@$(PYTHON) -m pip install -e /Users/erikh/code/carryall-baton-backend

clean:
	@rm -f sync.c1z
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
