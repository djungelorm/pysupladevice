.PHONY: build test test-cov publish

build:
	poetry build

test:
	poetry run pytest -v

test-cov:
	poetry run pytest --cov --cov-report=html -v

publish:
	poetry build
	poetry publish
