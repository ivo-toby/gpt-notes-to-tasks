from setuptools import setup, find_packages

setup(
    name="gpt-notes-to-tasks",
    version="0.1.0",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "openai",
        "langchain",
        "langchain-community",
        "chromadb",
        "tqdm",
        "tiktoken",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "pytest-mock",
            "black",
            "flake8",
            "mypy",
            "isort",
        ],
    },
    python_requires=">=3.8",
)