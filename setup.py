import os

from setuptools import setup, find_packages

# Define an empty dictionary to store the extracted constants
metadata = {}

# Create the full path to 'project_metadata.py'
metadata_file_path = os.path.join(os.getcwd(), 'logseg/project_metadata.py')

# Execute the 'project_metadata.py' file and capture the defined constants
with open(metadata_file_path) as metadata_file:
    exec(compile(metadata_file.read(), metadata_file_path, 'exec'), metadata)

setup(
    name=metadata.get("NAME"),
    version=metadata.get("VERSION"),
    description=metadata.get("DESCRIPTION"),
    long_description=metadata.get("LONG_DESCRIPTION"),
    author=metadata.get("AUTHOR"),
    author_email="garettsoftware@gmail.com",
    license="MIT",
    packages=find_packages(),
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
    python_requires=">=3.8.0",
    keywords="logging, multiprocessing, log segmentation, log rotation",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
