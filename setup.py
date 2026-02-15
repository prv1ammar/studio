from setuptools import setup, find_packages

setup(
    name="studio-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer[all]",
        "pydantic",
        "sqlmodel"
    ],
    entry_points={
        "console_scripts": [
            "studio-cli=backend.app.cli.main:app",
        ],
    },
)
