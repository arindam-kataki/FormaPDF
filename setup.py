from setuptools import setup, find_packages

setup(
    name="pdf-voice-editor",
    version="0.1.0",
    description="PDF editing application with voice commands",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "PyPDF2>=3.0.1",
        "pdfplumber>=0.10.3",
        "pymupdf>=1.23.14",
        "reportlab>=4.0.7",
        "SpeechRecognition>=3.10.0",
        "pyaudio>=0.2.13",
        "scikit-learn>=1.3.2",
        "PyQt6>=6.6.1",
        "spacy>=3.7.2",
        "opencv-python>=4.8.1.78",
    ],
    entry_points={
        "console_scripts": [
            "pdf-voice-editor=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)