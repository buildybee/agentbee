from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentbee",
    version="0.0.1",
    author="buildybee",
    author_email="paul.sayan@gmail.com",
    description="An AI-powered code assistant to analyze, assist with, and automate code modifications.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/buildybee/agentbee",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer[all]",
        "openai",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "agentbee=agentbee.main:app",
        ],
    },
)
