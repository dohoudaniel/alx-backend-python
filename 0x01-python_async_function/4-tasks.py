#!/usr/bin/env python3
"""
Take the code from wait_n from 1-concurrent_coroutines
and alter it into a new function task_wait_n. The code
is nearly identical to wait_n except task_wait_random is being called.
"""


# Import statements
import asyncio
from typing import List
task_wait_random = __import__('0-basic_async_syntax').wait_random


async def task_wait_n(n: int, max_delay: int) -> List[float]:
    """
    Returns a list of floats
    """
    firstList = []
    secondList = []
    #
    # Spawning wait_n n times with max_delay
    for i in range(n):
        spawn = task_wait_random(max_delay)
        firstList.append(spawn)
    #
    # Returning the final list
    for resolution in asyncio.as_completed((firstList)):
        calledDelay = await resolution
        secondList.append(calledDelay)
    #
    # Final return statement
    return secondList
