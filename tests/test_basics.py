from mplite import TaskManager,Task
import time


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
        
        
        
if __name__ == "__main__":
    test_alpha()
