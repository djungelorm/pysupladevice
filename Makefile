all:
	# nothing

test-cov:
	poetry run pytest --cov --cov-report=html -v

publish:
	poetry build
	poetry publish
