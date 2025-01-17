from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="app-video-cutter",
    version="1.0.0",
    author="Dimas Julianto",
    author_email="dimasjulianto96@gmail.com",
    description="A powerful tool for splitting videos using NVIDIA GPU acceleration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dimasjulianto/app-video-cutter",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.4.0",
        "psutil>=5.9.0",
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
        "nvidia-cuda-runtime-cu11>=11.8.0",
    ],
    entry_points={
        "console_scripts": [
            "video-cutter=src.gui:main",
        ],
    },
)