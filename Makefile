.PHONY: web-install web-run web-test web-lint

web-install:
	uv pip install -r web/requirements.txt

web-run:
	uv run uvicorn web.main:app --reload

web-test:
	python3 -m unittest discover -s web/tests -v

web-lint:
	uvx ruff check web/
