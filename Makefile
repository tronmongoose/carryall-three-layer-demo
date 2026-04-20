PYTHON ?= python3
AUTHORITY_RUNTIME_SRC ?= ../authority-runtime-python
CARRYALL_BATON_SRC    ?= ../carryall-baton-backend

.PHONY: demo setup clean layer2 layer3 verify

demo: layer2 pause layer3
	@echo
	@echo "--- end of demo ---"

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
	@$(PYTHON) -m pip install rich
	@$(PYTHON) -m pip install -e $(AUTHORITY_RUNTIME_SRC)
	@$(PYTHON) -m pip install -e $(CARRYALL_BATON_SRC)

clean:
	@rm -f sync.c1z
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
