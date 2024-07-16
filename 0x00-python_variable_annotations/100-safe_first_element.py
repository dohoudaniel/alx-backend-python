#!/usr/bin/env python3
"""
Duck Type Annotation
"""


# Import statements
from typing import Sequence, Union, Any  # List, Optional


# The types of the elements of the input are not known
def safe_first_element(lst: Sequence[Any]) -> Union[Any, None]:
    """
    Returns the first element of a list if it exists
    """
    if lst:
        return lst[0]
    else:
        return None
