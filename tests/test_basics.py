import os
import platform
import signal
from mplite import TaskManager, Task, TaskChain
import time
import traceback
import random

def test_alpha():
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


def f(*args, **kwargs):
    time.sleep(args[0])
    return args[0]/kwargs['hello']


def adder(a,b):
    return a+b


def broken(*args, **kwargs):
    raise NotImplementedError("this task must fail!")

    
def test_bad_inputs():
    try:
        Task(1)
        assert False, "f must be a callable"
    except TypeError:
        assert True

    try:
        Task(f, "bad input")
#         assert False, "*args must be None or a tuple"
    except TypeError:
        assert True
        
    try:
        Task(f, **("bad input"))
        assert False, "**kwargs must be a dict"
    except TypeError:
        assert True
        

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
        

def exit_kill():
    time.sleep(1)

    is_windows = platform.system() == "Windows"

    if is_windows:
        exit(-9)
    else:
        os.kill(os.getpid(), signal.SIGKILL)
    
    time.sleep(1)

    return "no err"

def exit_abrupt_exit():
    time.sleep(1)
    exit(42)

def test_killed():
    try:
        with TaskManager(1) as tm:
            res = tm.execute([Task(exit_kill)])

            print(res)

            raise Exception("Should have throw an exception")

    except ChildProcessError as ex:
        is_windows = platform.system() == "Windows"

        if is_windows:
            assert True
        else:
            assert "out of memory" in str(ex), "Must be out of memory exception"

def test_abrupt_exit():
    try:
        with TaskManager(1) as tm:
            res = tm.execute([Task(exit_abrupt_exit)])

            print(res)

            raise Exception("Should have throw an exception")

    except ChildProcessError as ex:
        assert "42" in str(ex), "Must be out of memory exception"


def task(index):
    time.sleep(random.random() * 2)

    return index


def test_task_order():

    tasks = [Task(task, (i, )) for i in range(10)]

    with TaskManager(10) as tm:
        res = [k for k, *_ in tm.execute(tasks)]

    assert res == list(range(10))

def test_task_chain_1():
    def foo(a):
        return a

    def post_2(prev, res):
        assert res == 2

        return Task(foo, 3)

    def post_1(prev, res):
        assert res == 1

        return TaskChain(
            Task(foo, 2),
            post_2
        )
    
    assert TaskChain(Task(foo, 1), next_task=post_1).execute() == 3

def foo(a):
    return a

def test_task_chain_2():

    def post_2(prev, res):
        assert res == 2

        return Task(foo, 3)

    def post_1(prev, res):
        assert res == 1

        return TaskChain(
            Task(foo, 2),
            post_2
        )
    
    tasks = [TaskChain(Task(foo, 1), next_task=post_1) for _ in range(5)]
    with TaskManager(len(tasks)) as tm:
        res = tm.execute(tasks)

    assert res == [3, 3, 3, 3, 3]

def task_exception(i):
    if i == 4:
        raise ValueError(f"my exception: {i}")
    
    return i

def test_exception_mode():
    tasks = [Task(task_exception, i) for i in range(10)]

    with TaskManager(10, error_mode="exception") as tm:
        try:
            [k for k, *_ in tm.execute(tasks)]
            assert False
        except Exception as e:
            assert tm.open_tasks == 0, "there should be no left-over tasks"
            assert str(e) == "my exception: 4", "wrong exception"
            assert isinstance(e, ValueError), "wrong exception type"
            assert type(e.__traceback__).__name__ == "traceback", "not a traceback"
            assert 'in task_exception\n    raise ValueError(f"my exception: {i}")\n' in traceback.format_tb(e.__traceback__)[-1], "wrong callstack"

if __name__ == "__main__":
    test_task_order()