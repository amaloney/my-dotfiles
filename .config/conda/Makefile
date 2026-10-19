PREFIX := ./.conda
LOCK := conda-lock.yml
SPEC := environment.yml
export CONDARC := $(CURDIR)/.condarc

.PHONY: help env lock clean
.DEFAULT_GOAL := help

help:
	@echo "Requires conda 26.5+ (built-in lockfiles)."
	@echo ""
	@echo "Usage:"
	@echo "  make env    rebuild ./.conda from conda-lock.yml (falls back to environment.yml)"
	@echo "  make lock   sync ./.conda to environment.yml, then regenerate conda-lock.yml"
	@echo "  make clean  delete ./.conda"

env:
	rm -rf $(PREFIX)
	@if [ -f $(LOCK) ]; then \
		conda create --yes -p $(PREFIX) --file $(LOCK); \
	else \
		echo "No $(LOCK) yet; solving from $(SPEC). Run 'make lock' and commit it."; \
		conda env create --yes -p $(PREFIX) -f $(SPEC); \
	fi

lock:
	@if [ -d $(PREFIX)/conda-meta ]; then \
		conda env update -p $(PREFIX) -f $(SPEC) --prune; \
	else \
		conda env create --yes -p $(PREFIX) -f $(SPEC); \
	fi
	# Platforms come from export_platforms in .condarc
	conda export -p $(PREFIX) --file $(LOCK)
	@echo "Updated $(LOCK). Commit it together with $(SPEC)."

clean:
	rm -rf $(PREFIX)
