# Environment name
ENV ?= default

# Paths derived from ENV
PREFIX := ./.conda/$(ENV)
ifeq ($(ENV),default)
  LOCK := conda-lock.yml
  SPEC := environment.yml
else
  LOCK := conda-lock-$(ENV).yml
  SPEC := environment-$(ENV).yml
endif

export CONDARC := $(CURDIR)/.condarc

.PHONY: help env lock clean
.DEFAULT_GOAL := help

help:
	@echo "Requires conda 26.5+ (built-in lockfiles)."
	@echo ""
	@echo "Usage:"
	@echo "  make env [ENV=name]    rebuild ./.conda/<name> from lockfile"
	@echo "  make lock [ENV=name]   sync environment and regenerate lockfile"
	@echo "  make clean [ENV=name]  delete ./.conda/<name>"
	@echo ""
	@echo "Environments: default (Python 3.14)"
	@echo ""
	@echo "Examples:"
	@echo "  make env               # build default environment"

env:
	@mkdir -p ./.conda && echo '**/*' > ./.conda/.gitignore
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

