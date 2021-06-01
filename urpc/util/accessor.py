from collections import Iterator
from collections import OrderedDict
from collections.abc import Mapping


# TODO: Lazy splitting is completely unnecessary and the implementation is awful. Refactor it out!
class ProcessorIter(Iterator):
    def __init__(self, processor, queue):
        self._processor = processor
        self._queue = queue

    def __next__(self):
        while True:
            if len(self._queue):
                return self._queue.pop(0)
            if not self._processor():
                raise StopIteration


class CommandIterMapping(Iterator):
    def __init__(self, commands):
        self._cmd_by_cid = OrderedDict([(cmd.cid, cmd) for cmd in commands])

    def __next__(self):
        try:
            cmd = self._cmd_by_cid.popitem(False)[1]
            return cmd
        except KeyError:
            raise StopIteration

    # Tries to find accessor counterpart
    # Returns setter/getter tuple and removes counterpart from iteration list in case of success
    def pop_counterpart(self, cmd):
        first_letter = cmd.cid[0]
        if first_letter not in ("g", "s"):
            raise ValueError("Has not getter/setter compatible CID!")
        # setter, getter = cmd
        other_cid = ("g" if first_letter == "s" else "s") + cmd.cid[1:]

        if other_cid not in self._cmd_by_cid:
            raise ValueError("Does not have counterpart!")

        other_cmd = self._cmd_by_cid[other_cid]
        setter, getter = (cmd, other_cmd) if first_letter == "s" else (other_cmd, cmd)

        empty_setter_response = len(setter.response.args) == 0
        empty_getter_request = len(getter.request.args) == 0
        valid_sign = empty_setter_response and empty_getter_request and setter.request.compare(getter.response)

        if not valid_sign:
            raise ValueError("Does not conform to getter/setter pair signature!")
        del self._cmd_by_cid[other_cid]
        return getter, setter


class Processor:
    def __init__(self, all_commands, **buffers):
        self._cmd_iter = CommandIterMapping(all_commands)
        self._commands = buffers["commands"]
        self._accessors = buffers["accessors"]

    def __call__(self, *args, **kwargs):
        try:
            cmd = next(self._cmd_iter)
            try:
                self._accessors.append(self._cmd_iter.pop_counterpart(cmd))
            except ValueError:
                self._commands.append(cmd)
            return True
        except StopIteration:
            return False


def split_by_type(all_commands):
    commands, accessors = [], []
    active = Processor(all_commands, commands=commands, accessors=accessors)
    return ProcessorIter(active, commands), ProcessorIter(active, accessors)


class LazyGroup(Iterator):
    def __init__(self, driver, group):
        self._driver = driver
        self._group = group
        self._index = 0

    def __next__(self):
        while len(self._driver[self._group]) <= self._index:
            if not self._driver():
                break
        else:
            item = self._driver[self._group][self._index]
            self._index += 1
            return item

        raise StopIteration()


class LazyGroupMapping:
    def __init__(self, driver):
        self._driver = driver

    def __getitem__(self, item):
        while True:
            if item in self._driver:
                return LazyGroup(self._driver, item)
            elif not self._driver():
                return []
                # raise KeyError("No elements in group {}".format(item))


class SimpleSortingDriver(Mapping):
    def __init__(self, iterable, sorter):
        self._iterable = iterable
        self._sorter = sorter
        self._seen = {}

    def __call__(self):
        try:
            el = next(self._iterable)
            self._seen.setdefault(self._sorter(el), []).append(el)
        except StopIteration:
            return False
        return True

    def __getitem__(self, item):
        return self._seen[item]

    def __contains__(self, item):
        return item in self._seen

    def __len__(self):
        return len(self._seen)

    def __iter__(self):
        return iter(self._seen)


def group_by(iterable, sorter, driver=SimpleSortingDriver):
    return LazyGroupMapping(driver(iter(iterable), sorter))


# if __name__ == "__main__":
#     test = [1, 2, 3, 42]
#     def sorter(item):
#         if item == 1:
#             return "one"
#         elif item == 2:
#             return "two"
#         elif item == 3:
#             return "four"
#         elif item == 42:
#             return "three"
#
#     groups = group_by(test, sorter)
#
#     for value in groups["four"]:
#         print(value)
