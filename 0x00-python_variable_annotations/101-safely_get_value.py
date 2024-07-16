#!/usr/bin/env python3
"""
"""


# Import statement
from typing import Mapping, Any, Union, TypeVar

T = TypeVar('T')


def safely_get_value(dct: Mapping, key: Any, \
    default: Union[T, None] = None) -> Union[Any, T]:
    """
    Returns the value of a key in a
    dictionary if it exists,
    otherwise returns a default value
    """
    if key in dct:
        return dct[key]
    else:
        return default
