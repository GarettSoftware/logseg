from setuptools import setup, find_packages

# Define metadata directly in setup.py to avoid circular import issues
NAME = "logseg"
VERSION = "0.3.0"
AUTHOR = "Garett MacGowan"
DESCRIPTION = "Python logging for multi-process and multi-threaded applications."
LONG_DESCRIPTION = (
    "Multiprocessing focused Python logger with easy-to-use log file segmentation for a better multiprocessing logging "
    "experience."
)

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=AUTHOR,
    author_email="garettsoftware@gmail.com",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[],
    extras_require={
        "docs": [
            "furo",
            "sphinx>=7.1.2",
            "myst_parser>=2.0.0",
            "sphinx-autoapi>=2.1.1",
            "sphinx-autobuild>=2021.3.14",
        ]
    },
    python_requires=">=3.9.13",
    keywords="logging, multiprocessing, log segmentation, log rotation",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
