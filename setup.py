from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kodekloud-engineer-tasks",
    version="1.0.0",
    author="KodeKloud",
    description="Testing framework for KodeKloud Engineer Tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pytest>=7.4.3",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
        "pyyaml>=6.0.1",
        "kubernetes>=28.1.0",
        "markdown>=3.5.1",
        "jsonschema>=4.20.0",
    ],
    extras_require={
        "dev": [
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)