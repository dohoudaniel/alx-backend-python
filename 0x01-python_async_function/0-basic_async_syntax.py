#!/usr/bin/env python3
"""
An Asynchronous coroutine that takes in an integer
argument that waits for a random delay between 0 and
the value of the argument, and eventually returns it.
The `random` module is used.
"""


# Import statements
import random
import asyncio


async def wait_random(max_delay=10) -> float:
    """
    Returns a random delay
    """
    wait = random.random() * max_delay
    await asyncio.sleep(wait)
    return wait
