#!/usr/bin/env python3
"""
A type-annotated function sum_list that
takes a list input_list of floats as
argument and returns their sum as a float.
"""


def sum_list(input_list: List[float]) -> float:
    """
    Return the sum of a list of floats.
    """
    return float(sum(input_list))
