import io
import multiprocessing
import traceback
import time
from tqdm import tqdm as _tqdm
import queue


major, minor, patch = 1, 2, 1
__version_info__ = (major, minor, patch)
__version__ = '.'.join(str(i) for i in __version_info__)


class Task(object):
    def __init__(self, f, *args, **kwargs) -> None:
        if not callable(f):
            raise TypeError(f"{f} is not callable")
        self.f = f
        if not isinstance(args, tuple):
            raise TypeError(f"{args} is not a tuple")
        self.args = args
        if not isinstance(kwargs, dict):
            raise TypeError(f"{kwargs} is not a dict")
        self.kwargs = kwargs
    def __str__(self) -> str:
        return f"Task(f={self.f.__name__}, *{self.args}, **{self.kwargs})"
    def __repr__(self) -> str:
        return f"Task(f={self.f.__name__}, *{self.args}, **{self.kwargs})"
    def execute(self):
        try:
            return self.f(*self.args,**self.kwargs)
        except Exception as e:
            f = io.StringIO()
            traceback.print_exc(limit=3, file=f)
            f.seek(0)
            error = f.read()
            f.close()
            return error
                    

class Worker(multiprocessing.Process):
    def __init__(self,name,tq,rq):
        super().__init__(group=None, target=self.update, name=name, daemon=False)
        self.exit = multiprocessing.Event()
        self.tq = tq  # workers task queue
        self.rq = rq  # workers result queue
    def update(self):
        while True:
            try:
                task = self.tq.get_nowait()
            except queue.Empty:
                task = None
            
            if task == "stop":
                self.tq.put_nowait(task)
                self.exit.set()
                break

            elif isinstance(task, Task):
                result = task.execute()
                self.rq.put(result)
            else:
                time.sleep(0.01)


class TaskManager(object):
    def __init__(self, cpu_count=None) -> None:
        self._cpus = multiprocessing.cpu_count() if cpu_count is None else cpu_count
        self.tq = multiprocessing.Queue()
        self.rq = multiprocessing.Queue()
        self.pool = []
        self._open_tasks = 0
    def __enter__(self):
        self.start()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb): # signature requires these, though I don't use them.
        self.stop()  # stop the workers.
    def start(self):
        for i in range(self._cpus):  # create workers
            worker = Worker(name=str(i), tq=self.tq, rq=self.rq)
            self.pool.append(worker)
            worker.start()
        while not all(p.is_alive() for p in self.pool):
            time.sleep(0.01)
    def execute(self, tasks, tqdm=_tqdm, pbar=None):
        """
        Execute tasks using mplite

        REQUIRED
        --------
        tasks: list
            List of tasks to execute

        OPTIONAL
        --------
        tqdm: Type[tqdm]
            Type[_tqdm]: (default) Use the standard tqdm module provided class.
            Type[tqdm]: A tqdm compatible callable.

            When progress bar is created, the given tqdm compatible callable will be used,
            if None is provided, falls back to the standard tqdm implementation.

        pbar: tqdm
            None: (default) Create a new progress bar using given tqdm callable.
            tqdm: An instance of tqdm progress bar.

            Tracks the execution progress using tqdm instance,
            if None is provided, progress bar will be created using tqdm callable provided by tqdm parameter.
        """
        self._open_tasks += len(tasks)
        for t in tasks:
            self.tq.put(t)
        results = []

        if pbar is None:
            """ if pbar object was not passed, create a new tqdm compatibe object """
            pbar = tqdm(total=self._open_tasks, unit='tasks')

        while self._open_tasks != 0:
            try:
                task = self.rq.get_nowait()
                self._open_tasks-=1
                results.append(task)
                pbar.update(1)
            except queue.Empty:
                time.sleep(0.01)
        return results

    def submit(self, task):
        """ permits asynchronous submission of tasks. """
        if not isinstance(task, Task):
            raise TypeError(f"expected mplite.Task, not {type(task)}")
        self._open_tasks += 1
        self.tq.put(task)

    def take(self):
        """ permits asynchronous retrieval of results """
        try:
            result = self.rq.get_nowait()
            self._open_tasks-=1
        except queue.Empty:
            result = None
        return result

    @property
    def open_tasks(self):
        return self._open_tasks

    def stop(self):
        for _ in range(self._cpus):
            self.tq.put('stop')
        while any(p.is_alive() for p in self.pool):
            time.sleep(0.01)
        self.pool.clear()
        while not self.tq.empty:
            _ = self.tq.get_nowait()
        while not self.rq.empty:
            _ = self.rq.get_nowait()





