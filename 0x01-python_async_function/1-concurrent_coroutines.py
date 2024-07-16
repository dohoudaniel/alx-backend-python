#!/usr/bin/env python3
"""
An async routine that takes in 2 int arguments,
n and max_delay. Then, it spawns wait_random n
times with the specified max_delay.

wait_random is imported from 0-basic_async_syntax.py
and returns the list of all the delays (float values).
The list of delays should be in an ascending order
"""


# Import statements
import asyncio
from typing import List
wait_random = __import__('0-basic_async_syntax').wait_random


async def wait_n(n: int, max_delay: int) -> List[float]:
    """
    Returns a list of floats
    """
    firstList = []
    secondList = []
    #
    # Spawning wait_n n times with max_delay
    for i in range(n):
        spawn = wait_random(max_delay)
        firstList.append(spawn)
    #
    # Returning the final list
    for resolution in asyncio.as_completed((firstList)):
        calledDelay = await resolution
        secondList.append(calledDelay)
    #
    # Final return statement
    return secondList
