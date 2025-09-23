#!/usr/bin/env python3
"""Test runner script for KodeKloud Engineer Tasks."""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True
    )
    return result.returncode, result.stdout, result.stderr


def main():
    """Main test runner."""
    print("=" * 60)
    print("KodeKloud Engineer Tasks - Test Suite")
    print("=" * 60)

    # Install dependencies
    print("\n📦 Installing dependencies...")
    code, stdout, stderr = run_command("pip install -q -r requirements.txt")
    if code != 0:
        print(f"❌ Failed to install dependencies: {stderr}")
        return 1

    code, stdout, stderr = run_command("pip install -q -e .")
    if code != 0:
        print(f"❌ Failed to install package: {stderr}")
        return 1

    print("✅ Dependencies installed")

    # Run linting
    print("\n🔍 Running linting checks...")
    code, stdout, stderr = run_command("flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503")
    if code != 0:
        print(f"⚠️  Linting warnings:\n{stdout}")
    else:
        print("✅ Linting passed")

    # Run type checking
    print("\n🔍 Running type checks...")
    code, stdout, stderr = run_command("mypy src/ --ignore-missing-imports")
    if code != 0:
        print(f"⚠️  Type checking warnings:\n{stdout}")
    else:
        print("✅ Type checking passed")

    # Run unit tests
    print("\n🧪 Running unit tests...")
    code, stdout, stderr = run_command("pytest tests/unit/ -v -m unit")
    if code != 0:
        print(f"❌ Unit tests failed:\n{stdout}\n{stderr}")
        return 1
    print("✅ Unit tests passed")

    # Run integration tests
    print("\n🔗 Running integration tests...")
    code, stdout, stderr = run_command("pytest tests/integration/ -v -m integration")
    if code != 0:
        print(f"❌ Integration tests failed:\n{stdout}\n{stderr}")
        return 1
    print("✅ Integration tests passed")

    # Run edge case tests
    print("\n🔮 Running edge case tests...")
    code, stdout, stderr = run_command("pytest tests/edge/ -v -m edge")
    if code != 0:
        print(f"❌ Edge case tests failed:\n{stdout}\n{stderr}")
        return 1
    print("✅ Edge case tests passed")

    # Run coverage report
    print("\n📊 Generating coverage report...")
    code, stdout, stderr = run_command(
        "pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml"
    )

    if code != 0:
        print(f"❌ Tests with coverage failed:\n{stdout}\n{stderr}")
        return 1

    # Extract coverage percentage
    for line in stdout.split('\n'):
        if 'TOTAL' in line:
            print(f"\n📈 Coverage Summary: {line.strip()}")
            break

    print("\n✅ All tests passed successfully!")
    print(f"📄 HTML coverage report: {Path('htmlcov/index.html').absolute()}")
    print(f"📄 XML coverage report: {Path('coverage.xml').absolute()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())