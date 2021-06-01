import re
from os import walk
from os.path import join
from typing import List, Generator

__all__ = ["resources"]


def resources(path: str) -> Generator[str, None, None]:
    for root, dirs, files in walk(path, followlinks=True):
        filtered_dirs = __filter_files(dirs)
        dirs.clear()
        dirs.extend(filtered_dirs)

        for name in __filter_files(files):
            yield join(root, name)


__files_filter_regex = re.compile("^(\\.git.*|\\.hg.*)$")


def __filter_files(files: List[str]) -> List[str]:
    return list(filter(lambda name: __files_filter_regex.match(name) is None, files))
