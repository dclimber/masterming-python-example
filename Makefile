PHONY: test

test:
	PYTHONPATH=./src python -m unittest discover tests/
