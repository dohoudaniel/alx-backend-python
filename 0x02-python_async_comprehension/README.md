#### Python: Async Comprehension

In this directory, I learn about Async Comprehensions in Python, and how they are used to yield values.

Some of the concepts I learned in this project:
- Asynchronous Generators
- Asynchronous Comprehensions (and their results):
    - Set Comprehensions: `{i async for i in agen()}`
    - List Comprehensions: `[i async for i in agen()]`
    - Dict Comprehensions: `{i: i ** 2 async for i in agen()}`
    - Generator Comprehensions: `(i ** 2 async for i in agen())`
- Pratical Use Cases Of Asynchronous Comprehensions And Generators:
    - Data Streaming
    - Web Scraping
    - I/O Operations
- Using `asyncio.gather()`
