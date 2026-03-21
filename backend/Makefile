# StockIntel Backend – Test & Quality Commands
# Usage: cd backend && make <target>

.PHONY: test test-cov lint install-test help

help:
	@echo "Available targets:"
	@echo "  install-test  Install test dependencies"
	@echo "  test          Run all tests"
	@echo "  test-cov      Run tests with coverage report"
	@echo "  lint          Run static analysis (ast-based)"

install-test:
	pip install pytest pytest-cov pytest-asyncio httpx

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=70

lint:
	python3 -c "\
import ast, os; \
APP='app'; issues=[]; \
[issues.append(('W',f,e.lineno,'bare except')) \
 for root,dirs,files in os.walk(APP) \
 for f in files if f.endswith('.py') \
 for e in ast.walk(ast.parse(open(os.path.join(root,f),'rb').read())) \
 if isinstance(e,ast.ExceptHandler) and e.type is None]; \
print(f'{len(issues)} bare-except issues found') if issues else print('Lint: OK')"
