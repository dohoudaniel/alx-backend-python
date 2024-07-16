#!/usr/bin/env python3
"""
A coroutine, taking no argument, but
loops 10 times, each time, asynchronously
waiting for 1 second, then yielding a
random number between 0 and 10
The random module is used
"""


# Import statements
import random
import asyncio
from typing import Generator


async def async_generator() -> Generator[float, None, None]:
    """
    Yields a random number between 0 and 10
    """
    for i in range(10):
        await asyncio.sleep(1)
        my_random_number = random.random * 10
        yield my_random_number
