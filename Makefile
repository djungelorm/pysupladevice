.PHONY: setup test dist coverage lint typecheck clean

setup: clean
	DEB_PYTHON_INSTALL_LAYOUT="deb" virtualenv env
	env/bin/pip install -e .[dev]
	env/bin/pre-commit install

test:
	env/bin/pre-commit run --all-files

dist:
	rm -rf dist
	env/bin/python -m build
	env/bin/python -m build --wheel

coverage:
	env/bin/pytest --cov pysupladevice --cov tests --cov-report=html:htmlcov

lint:
	env/bin/pre-commit run --all-files pylint

typecheck:
	env/bin/pre-commit run --all-files mypy

clean:
	rm -rf env build dist *.egg-info
