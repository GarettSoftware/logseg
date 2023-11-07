import os

from pathlib import Path

from typing import Union

from shutil import rmtree


def create_dir_if_not_exists(directory: Union[Path, str]) -> None:
    """
    This function creates a directory if it doesn't already exist.
    Args:
        directory: The directory to create (either a Path or a path string)

    Returns:

    """
    if not os.path.isdir(directory):
        os.makedirs(directory)


def delete_dir_contents_if_exists(directory: Union[Path, str]) -> None:
    """
    This function deletes the contents of a directory if it exists.
    Args:
        directory: The directory to delete the contents of (either a Path or a path string)

    Returns:

    """
    if not os.path.isdir(directory):
        return

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            rmtree(file_path)
