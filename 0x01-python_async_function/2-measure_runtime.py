#!/usr/bin/env python3
"""
A function that takes in two integers as
arguments and measures the total execution
time for wait_n(n, max_delay), and returns
the total time / n.
This function should return a float
"""


# Import statements
import asyncio
import time
wait_n = __import__('1-concurrent_coroutines').wait_n


async def measure_time(n: int, max_delay: int) -> float:
    """
    Returns the total execution time
    """
    start_time = time.time()
    await asyncio.run(wait_n(n, max_delay))
    end_time = time.time()
    execution_time = end_time - start_time
    return (execution_time / n)
