#!/usr/bin/env python3
"""
Duck Type Annotation
"""


# Import statements
from typing import List, Optional, Any


# The types of the elements of the input are not known
def safe_first_element(lst: List[Any]) -> Optional[Any]:
    """
    Returns the first element of a list if it exists
    """
    if lst:
        return lst[0]
    else:
        return None
