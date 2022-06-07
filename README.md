# mplite

![Build status](https://github.com/root-11/mplite/actions/workflows/python-package.yml/badge.svg)
[![codecov](https://codecov.io/gh/root-11/mplite/branch/main/graph/badge.svg?token=QRBR8W5AB3)](https://codecov.io/gh/root-11/mplite)
[![Downloads](https://pepy.tech/badge/mplite)](https://pepy.tech/project/mplite)
[![Downloads](https://pepy.tech/badge/mplite/month)](https://pepy.tech/project/mplite/month)

A light weight wrapper for pythons multiprocessing module that makes multiprocessing easy.

In case anyone is looking for a very easy way to use multiprocessing with args and kwargs, here is a neat wrapper as [mplite](https://pypi.org/project/mplite/):

The [test](https://github.com/root-11/mplite/blob/main/tests/test_basics.py) is also the showcase:
```
from mplite import TaskManager, Task
import time

# first create the function that each cpu should work on individually.
def f(*args, **kwargs):
    print(args, kwargs)
    time.sleep(args[0])
    return args[0]

# Next create the main function you'd like to run everything from:
def main():
    tasks = []   # create a tasklist and populate it with tasks
    for n in list(range(10))*5:
        t = Task(f, *(n/10,), **{'hello': n})  
        tasks.append(t)

    with TaskManager() as tm:
        results = tm.execute(tasks)

    print(results)

if __name__ == "__main__":
    main()
```
Note that tasks can't crash. In case of exceptions during
task execution, the traceback is captured and the compute
core continues to execute the next task.

Also, if you want to check that the inputs to the task
are formed correctly, you can do the check from the interpreter,
by calling `.execute()` on the task:

```
>>> t = Task(f, *(1,2,3), **{"this":42})
>>> t.execute()
```
