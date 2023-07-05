import logging
import sys
import pathlib
import inspect

# import datetime

from typing import Any

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s - %(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


def poslog(_message: str) -> None:
    "log debug message with it's position on code lines"
    logging.debug(
        f"-> {pathlib.Path(inspect.getframeinfo(inspect.currentframe().f_back).filename).name!r} : [:{sys._getframe(1).f_lineno}:] : {_message}"
    )


def shortened_content(_content: str, _len: int = 8) -> str:
    _content, *_ = _content.partition("\n")
    if len(_content) < _len:
        return _content
    more = "..."
    _len -= len(more)
    return _content[:_len] + more


# chatgpt help :)
def divide_list(lst, divider):
    if divider > len(lst):
        raise ValueError("Divider cannot be greater than the length of the list.")

    # quotient = len(lst) // divider
    # remainder = len(lst) % divider
    quotient, remainder = divmod(len(lst), divider)

    sublists = []
    start = 0

    for _ in range(divider):
        sublist_length = quotient + 1 if remainder > 0 else quotient
        sublists.append(tuple(lst[start : start + sublist_length]))
        start += sublist_length
        remainder -= 1

    return tuple(sublists)


# chatgpt again ! in hurry gotta go
def divide_dict(dct, divider):
    if divider <= 0 or divider > len(dct):
        raise ValueError("Invalid divider")

    keys = list(dct.keys())
    piece_size = len(keys) // divider
    remainder = len(keys) % divider

    result_dict = {}
    start = 0

    for i in range(divider):
        end = start + piece_size + (1 if i < remainder else 0)
        sub_dict = {key: dct[key] for key in keys[start:end]}
        result_dict[i] = sub_dict
        start = end

    return result_dict


def convert_todo_check(_check: bool) -> str:
    return "[x]" if _check else "[ ]"


if __name__ == "__main__":
    arr = [1, 2, 3, 5, 6, 7, 8, 9, 0]
    abb = {1: 2, 2: 3, 3: 4, 4: 5}

    print(abb)
    print(divide_dict(abb, 2))

    # poslog("Hello, Worlds!")
