.PHONY: web-install web-run web-test web-lint test validate

web-install:
	uv pip install -r web/requirements.txt

web-run:
	uv run uvicorn web.main:app --reload

web-test:
	python3 -m unittest discover -s web/tests -v

web-lint:
	uvx ruff check web/

# Full offline test sweep: web layer + RAG/planning package + self-improvement adversarial suite.
test:
	python3 -m unittest discover -s web/tests -v
	python3 -m unittest discover -s n8n_rag_system/tests -v
	python3 -B -m unittest discover -s tests/self_improvement -v

# Project + security-control validator. Exit 0 means all merged-project checks pass.
validate:
	python3 scripts/validate-project.py
