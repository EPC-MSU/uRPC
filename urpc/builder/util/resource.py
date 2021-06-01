import re
from os import walk
from os.path import join
from typing import List, Generator

__all__ = ["resources"]


def resources(path: str) -> Generator[str, None, None]:
    for root, dirs, files in walk(path, followlinks=True):
        filtered_dirs = __filter_dirs(dirs)
        dirs.clear()
        dirs.extend(filtered_dirs)

        for name in files:
            yield join(root, name)


__dir_filter_regex = re.compile("^(\\.git|\\.hg)$")


def __filter_dirs(dirs: List[str]) -> List[str]:
    return list(filter(lambda dir_name: __dir_filter_regex.match(dir_name) is None, dirs))
