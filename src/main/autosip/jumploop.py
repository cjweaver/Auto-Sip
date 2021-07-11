import logging
import random
from typing import List


log = logging.getLogger(_name_)


class FileError(RuntimeError):
    """Error raised when a file operation fails."""


def fo0(p):
    pass


def fo1(p):
    if random.random() < 0.05:
        raise FileError("Eugh, something happend")


def fo2(p):
    pass


def process_one_file(path):
    for file_operation in [fo0, fo1, fo2]:
        file_operation(path)


def process_all_files(files: List[str]):
    for path in files:
        try:
            process_one_file(path)
        except FileError:
            log.exception(f"Processing of {path} failed")
        else:
            log.info(f"Processed {path}")


if _name_ == "_main_":
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.INFO)
    files = [f"foo{x}" for x in range(100)]
    process_all_files(files)
