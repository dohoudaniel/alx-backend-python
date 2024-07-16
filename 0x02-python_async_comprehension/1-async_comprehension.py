#!/usr/bin/env python3
"""
Imports the async_generator function
from 0-async_generator and then uses
a coroutine that takes no argument
to collect 10 random numbers using
an async comprehensing over async_generator,
then returns the 10 random numbers
"""


# Import statements
async_generator = __import__('0-async_generator').async_generator
from typing import List
import asyncio


async def async_comprehension() -> List[float]:
    """
    Returns a list of the ten random
    numbers that async_generator returns
    """
    results = [i async for i in async_generator()]
    return results
