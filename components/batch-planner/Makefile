.PHONY: test lint clean

test:
	pytest tests/ -v

lint:
	python -m py_compile scripts/batch_manager.py scripts/util.py
	@echo "✓ Syntax OK"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
