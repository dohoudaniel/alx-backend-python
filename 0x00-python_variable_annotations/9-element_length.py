#!/usr/bin/env python3
"""
A function that takes in a list,
loops through the list, and returns
a list of the lengths of each element.
"""


from typing import List, Iterable, Tuple, Sequence


def element_length(lst: Iterable[Sequence]) -> List[Tuple[Sequence, int]]:
    """
    Returns a list of tupleses
    """
    return [(i, len(i)) for i in lst]
