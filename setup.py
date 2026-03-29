from setuptools import setup, find_packages

setup(
    name="video-analyzer",
    version="1.0.0",
    description="Analyze video files and build a metadata + AI content catalog",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "ollama>=0.4.0",
    ],
    entry_points={
        "console_scripts": [
            "video-analyzer=video_analyzer.cli:main",
        ],
    },
)
