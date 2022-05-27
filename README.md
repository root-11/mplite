# mplite
A light weight wrapper for pythons multiprocessing module that makes multiprocessing easy.

In case anyone is looking for a very easy way to use multiprocessing with args and kwargs, here is a neat wrapper as [mplite](https://pypi.org/project/mplite/):

The [test](https://github.com/root-11/mplite/blob/main/tests/test_basics.py) is also the showcase:
```
from mplite import TaskManager, Task

# first create the function that each cpu should work on individually.
def f(*args, **kwargs):
    print(args, kwargs)
    time.sleep(args[0])
    return args[0]

# Next create the main function you'd like to run everything from:
def mr_main():

    task_list = []   # create a tasklist and populate it with tasks
    for n in list(range(10)*5:
        t = Task(f, *(n/10,), **{'hello': n})  
        task_list.append(t)

    with TaskManager() as tm:
        results = tm.execute(tasks)

if __name__ == "__main__":
    mr_main()
```

