from mplite import TaskManager,Task
import time


def test_alpha():
    args = list(range(10)) * 5
    start = time.time()
    
    with TaskManager() as tm:
        # add the first tasks
        tasks = [Task(f, *(arg/10,), **{'hello': arg}) for arg in args]    
        results = tm.execute(tasks)  
        
        end = time.time()
        print(f"did nothing for {end-start} seconds, producing {results} result")
        
        # add more tasks to the same pool of workers:
        tasks = [Task(broken, *(i,)) for i in range(3)]
        results = tm.execute(tasks)
        for result in results:
            print(result)  # this will print tracebacks!

def f(*args, **kwargs):
    print(args, kwargs)
    time.sleep(args[0])
    return args[0]

def broken(*args, **kwargs):
    raise NotImplementedError("this task must fail!")


if __name__ == "__main__":
    test_alpha()
