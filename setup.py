"""Setup configuration for loop-ai package."""

from setuptools import setup, find_packages

setup(
    name="loop-engineering-ai",
    version="0.1.0",
    description="Loop Engineering AI: Guarded autonomous repair loop for software repositories.",
    author="Loop Engineering AI Team",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "loop-ai = loop_ai.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
