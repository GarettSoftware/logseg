from setuptools import setup, find_packages

from logseg.project_metadata import NAME, VERSION, DESCRIPTION, LONG_DESCRIPTION, AUTHOR

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
