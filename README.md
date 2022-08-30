# mplite

![Build status](https://github.com/root-11/mplite/actions/workflows/python-package.yml/badge.svg)
[![codecov](https://codecov.io/gh/root-11/mplite/branch/main/graph/badge.svg?token=QRBR8W5AB3)](https://codecov.io/gh/root-11/mplite)
[![Downloads](https://pepy.tech/badge/mplite)](https://pepy.tech/project/mplite)
[![Downloads](https://pepy.tech/badge/mplite/month)](https://pepy.tech/project/mplite/month)

A light weight wrapper for pythons multiprocessing module that makes multiprocessing easy.

In case anyone is looking for a very easy way to use multiprocessing with args and kwargs, here is a neat wrapper as [mplite](https://pypi.org/project/mplite/):

The [test](https://github.com/root-11/mplite/blob/main/tests/test_basics.py) is also the showcase:

*1. get the imports*

```
from mplite import TaskManager, Task
import time
```

*2. Create the function that each cpu should work on individually.*

```
def f(*args, **kwargs):
    time.sleep(args[0])
    return args[0]/kwargs['hello']
```

*2.1. I also add a function that will fail to illustrate that the TaskManager doesn't crash...*
```
def broken(*args, **kwargs):
    raise NotImplementedError("this task must fail!")
```


*3. create the main function you'd like to run everything from:*

```
def main():
    args = list(range(10)) * 5
    start = time.time()
    
    with TaskManager() as tm:
        # add the first tasks
        tasks = [Task(f, *(arg/10,), **{'hello': arg}) for arg in args]

        print("an example of a tasks is available as string:\n\t", str(tasks[0]), '\n\t', repr(tasks[0]))

        results = tm.execute(tasks)   # this will contain results and tracebacks!
        
        end = time.time()
        print(f"did nothing for {end-start} seconds, producing {len(results)} results")
        print(f"hereof {len([result for result in results if isinstance(result, str) ])} had errors.")
        print(f"the rest where results: {[i for i in results if not isinstance(i,str)]}")
        
        # add more tasks to the SAME pool of workers:
        tasks = [Task(broken, *(i,)) for i in range(3)]
        results = tm.execute(tasks)
        print("More expected errors:")
        for result in results:
            print("expected -->", result)  

if __name__ == "__main__":
    main()
```

*Expected outputs*

```
an example of a tasks is available as string:
	 Task(f=f, *(0.0,), **{'hello': 0}) 
	 Task(f=f, *(0.0,), **{'hello': 0})

  0%|          | 0/50 [00:00<?, ?tasks/s]
  2%|▏         | 1/50 [00:00<00:07,  6.96tasks/s]
  4%|▍         | 2/50 [00:00<00:06,  7.75tasks/s]
  6%|▌         | 3/50 [00:00<00:05,  8.15tasks/s]
 14%|█▍        | 7/50 [00:00<00:03, 14.16tasks/s]
 18%|█▊        | 9/50 [00:00<00:02, 14.36tasks/s]
 24%|██▍       | 12/50 [00:00<00:02, 14.13tasks/s]
 32%|███▏      | 16/50 [00:01<00:01, 17.34tasks/s]
 38%|███▊      | 19/50 [00:01<00:01, 18.03tasks/s]
 42%|████▏     | 21/50 [00:01<00:01, 16.66tasks/s]
 46%|████▌     | 23/50 [00:01<00:01, 15.06tasks/s]
 52%|█████▏    | 26/50 [00:01<00:01, 17.60tasks/s]
 56%|█████▌    | 28/50 [00:01<00:01, 16.86tasks/s]
 62%|██████▏   | 31/50 [00:02<00:01, 16.72tasks/s]
 66%|██████▌   | 33/50 [00:02<00:00, 17.37tasks/s]
 70%|███████   | 35/50 [00:02<00:00, 17.72tasks/s]
 74%|███████▍  | 37/50 [00:02<00:00, 17.52tasks/s]
 80%|████████  | 40/50 [00:02<00:00, 19.88tasks/s]
 86%|████████▌ | 43/50 [00:02<00:00, 15.19tasks/s]
 90%|█████████ | 45/50 [00:02<00:00, 13.69tasks/s]
 94%|█████████▍| 47/50 [00:03<00:00, 14.46tasks/s]
 98%|█████████▊| 49/50 [00:03<00:00, 10.98tasks/s]
100%|██████████| 50/50 [00:03<00:00, 14.40tasks/s]

did nothing for 3.601374387741089 seconds, producing 50 results
hereof 5 had errors.
the rest where results: [0.1, 0.1, 0.0999..., 0.1, 0.1, 0.1, 0.1, 0.0999..., 0.0999..., 0.0999..., 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.0999..., 0.0999..., 0.0999..., 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.0999..., 0.0999..., 0.0999..., 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.0999..., 0.0999..., 0.0999..., 0.1, 0.1, 0.1, 0.1, 0.0999..., 0.0999..., 0.1, 0.1]

  0%|          | 0/3 [00:00<?, ?tasks/s]
100%|██████████| 3/3 [00:00<00:00, 80.66tasks/s]

More expected errors:

expected --> Traceback (most recent call last):
  File "d:\github\mplite\mplite\__init__.py", line 97, in execute
    return self.f(*self.args,**self.kwargs)
  File "d:\github\mplite\tests\test_basics.py", line 36, in broken
    raise NotImplementedError("this task must fail!")
NotImplementedError: this task must fail!

expected --> Traceback (most recent call last):
  File "d:\github\mplite\mplite\__init__.py", line 97, in execute
    return self.f(*self.args,**self.kwargs)
  File "d:\github\mplite\tests\test_basics.py", line 36, in broken
    raise NotImplementedError("this task must fail!")
NotImplementedError: this task must fail!

expected --> Traceback (most recent call last):
  File "d:\github\mplite\mplite\__init__.py", line 97, in execute
    return self.f(*self.args,**self.kwargs)
  File "d:\github\mplite\tests\test_basics.py", line 36, in broken
    raise NotImplementedError("this task must fail!")
NotImplementedError: this task must fail!

```

Note that tasks **can't crash**! In case of exceptions during
task execution, the traceback is captured and the compute
core continues to execute the next task.

### How to test worker functions

Also, if you want to check that the inputs to the task
are formed correctly, you can do the check from the interpreter,
by calling `.execute()` on the task:

```
>>> t = Task(f, *(1,2,3), **{"this":42})
>>> t.execute()
```

### How to handle incremental tasks

From version 1.1.0 it is possible to add tasks incrementally.

Let's say I'd like to solve the pyramid task where I add up all numbers

```
1+2  3+4  5+6  7+8  9+10
 =    =    =    =    = 
 3 +  7    11 + 15   19
   =         =       =
   10        26  +  19
   =             =
   10      +     45
           = 
          55
```

This requires that I:

1. create a queue with 1,2,3,...,10
2. add tasks for the numbers to be added pairwise
3. receive the result
4. when I have a pair of numbers submit them AGAIN.

Here is an example of what the code can look like:
```

def test_incremental_workload():
    with TaskManager() as tm:       
        # 1. create initial workload
        checksum = 55
        for a in range(1,10,2):
            t = Task(adder, a, a+1)
            print(t)
            tm.submit(t)
    
        # 2. create incremental workload
        a,b = None,None
        while True:
            result = tm.take()
            if result is None:
                if tm.open_tasks == 0:
                    break
                else:
                    continue
            
            if a is None:
                a = result
            else:
                b = result
            
            if a and b:
                t = Task(adder, a,b)
                print(t)
                tm.submit(t)
                a,b = None,None

        print(a,b,flush=True)
        assert a == checksum or b == checksum,(a,b,checksum)


```

Output:
```
Task(f=adder, *(1, 2), **{})
Task(f=adder, *(3, 4), **{})
Task(f=adder, *(5, 6), **{})
Task(f=adder, *(7, 8), **{})
Task(f=adder, *(9, 10), **{})
Task(f=adder, *(3, 7), **{})
Task(f=adder, *(11, 15), **{})
Task(f=adder, *(19, 10), **{})
Task(f=adder, *(26, 29), **{})
55 None

```

Use mplite wisely. Executing each tasks has a certain overhead associated with it. 
The fewer the number of tasks and the heavier (computationally) each of them the better.

Example with number of calls with a number of iterations in the call:
```
def run_calcs_calls(mp_enabled=True, rng=50_000_000, calls = 20):
    start = time.time()
    L = []
    if mp_enabled:
        with TaskManager() as tm:
            tasks = []
            for call in range(1, calls+1):
                tasks.append(Task(fun, *(call, rng)))
            L = tm.execute(tasks)
    else:
        for call in range(1, calls+1):
            res = fun(call, rng)
            L.append(res)

    end = time.time()
    if mp_enabled:
        print('mplite - enabled')
    else:
        print('mplite - disabled')

    print('time taken: ', end - start)
    print(L)


def fun(call_id, rng):
    # burn some time iterating thru
    t = 0
    for i in range(rng):
        t = i/call_id
    return t

def test_mplite_performance():    
    # change calls and range to see the knock on effect on performance
    print('========CALLS TEST===========')
    calls = 10 # number of calls
    rng = 50_000_000 # iterations in the call to spend some time calculating
    print('calls: ', calls, ', range: ', rng)
    run_calcs_calls(True, rng, calls)
    run_calcs_calls(False, rng, calls)
    print()
    calls = 2000 # number of calls
    rng = 50 # iterations in the call to spend some time calculating
    print('calls: ', calls, ', range: ', rng)
    run_calcs_calls(True, rng, calls)
    run_calcs_calls(False, rng, calls)
```

Output:
```
========CALLS TEST===========
calls:  10 , range:  50000000
mplite - enabled
time taken:  3.9659698009490967
mplite - disabled
time taken:  16.89996838569641

calls:  2000 , range:  50
mplite - enabled
time taken:  0.7209787368774414
mplite - disabled
time taken:  0.004016399383544922

```

Example with sleep time in each adder function:
```
def run_calcs_sleep(mp_enabled, sleep):
    args = list(range(20))
    start = time.time()
    prev_mem = 0
    L = []

    if mp_enabled:
        with TaskManager() as tm:
            tasks = []
            for arg in args:
                tasks.append(Task(adder, *(prev_mem, arg, sleep)))
                prev_mem = arg
            L = tm.execute(tasks)
    else:
        for arg in args:
            res = adder(prev_mem, arg, sleep)
            L.append(res)
            prev_mem = arg

    end = time.time()
    if mp_enabled:
        print('mplite - enabled')
    else:
        print('mplite - disabled')

    print('time taken: ', end - start)
    print(L)


def adder(a, b, sleep):
    time.sleep(sleep)
    return a+b

def test_mplite_performance():    
def test_mplite_performance():

    # change sleep times to see the knock on effect on performance
    print('========SLEEP TEST===========')
    sleep = 2
    print('sleep timer value: ', sleep)
    run_calcs_sleep(True, sleep)
    run_calcs_sleep(False, sleep)
    print()
    sleep = 0.02
    print('sleep timer value: ', sleep)
    run_calcs_sleep(True, sleep)
    run_calcs_sleep(False, sleep)
    sleep = 0.01
    print('sleep timer value: ', sleep)
    run_calcs_sleep(True, sleep)
    run_calcs_sleep(False, sleep)
```

Output:
```
========SLEEP TEST===========
sleep timer value:  2
mplite - enabled
time taken:  4.644009828567505
mplite - disabled
time taken:  40.01024603843689

sleep timer value:  0.02
mplite - enabled
time taken:  0.6609671115875244
mplite - disabled
time taken:  0.4100008010864258

sleep timer value:  0.01
mplite - enabled
time taken:  0.6430003643035889
mplite - disabled
time taken:  0.21017980575561523



```
