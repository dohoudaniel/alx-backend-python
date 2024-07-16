#!/usr/bin/env python3
"""
A function that takes an integer
and returns an asyncio.Task
"""


# Import statement
import asyncio
wait_random = __import__('0-basic_async_syntax').wait_random


def task_wait_random(max_delay: int) -> asyncio.Task:
    """
    Returns an asyncio.task
    """
    return asyncio.Task(wait_random(max_delay))
