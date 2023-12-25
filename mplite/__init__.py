import io
import sys
import multiprocessing
import traceback
import time
from tqdm import tqdm as _tqdm
import queue
from itertools import count
from multiprocessing.context import BaseContext

major, minor, patch = 1, 2, 6
__version_info__ = (major, minor, patch)
__version__ = '.'.join(str(i) for i in __version_info__)
default_context = "spawn"

class Task(object):
    task_id_counter = count(start=1)

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
        self.id = next(Task.task_id_counter)

    def __str__(self) -> str:
        return f"Task(f={self.f.__name__}, *{self.args}, **{self.kwargs})"

    def __repr__(self) -> str:
        return f"Task(f={self.f.__name__}, *{self.args}, **{self.kwargs})"

    def execute(self):
        try:
            return self.f(*self.args, **self.kwargs)
        except Exception as e:
            f = io.StringIO()
            traceback.print_exc(limit=3, file=f)
            f.seek(0)
            error = f.read()
            f.close()
            return error


class Worker(object):
    def __init__(self, ctx: BaseContext, name: str, tq: multiprocessing.Queue, rq: multiprocessing.Queue, init: Task):
        """
        Worker class responsible for executing tasks in parallel, created by TaskManager.

        REQUIRED
        --------
        ctx: BaseContext
            Process spawning context ForkContext/SpawnContext. Note: Windows cannot fork.
        name: str
            Name of the worker process.
        tq: Queue
            Task queue
        rq: Queue
            Result queue
        init: Task
            Task executed when worker starts.
        """
        self.ctx = ctx
        self.exit = ctx.Event()
        self.tq = tq  # workers task queue
        self.rq = rq  # workers result queue
        self.init = init

        self.process = ctx.Process(group=None, target=self.update, name=name, daemon=False)

    def start(self):
        self.process.start()

    def is_alive(self):
        return self.process.is_alive()
    
    @property
    def exitcode(self):
        return self.process.exitcode

    def update(self):
        if self.init:
            self.init.f(*self.init.args, **self.init.kwargs)

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
                self.rq.put((task.id, result))
            else:
                time.sleep(0.01)


class TaskManager(object):
    def __init__(self, cpu_count: int = None, context=default_context, worker_init: Task = None) -> None:
        self._ctx = multiprocessing.get_context(context)
        self._cpus = multiprocessing.cpu_count() if cpu_count is None else cpu_count
        self.tq = self._ctx.Queue()
        self.rq = self._ctx.Queue()
        self.pool: list[Worker] = []
        self._open_tasks = 0

        assert worker_init is None or isinstance(worker_init, Task)

        self.worker_init = worker_init

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # signature requires these, though I don't use them.
        self.stop()  # stop the workers.

    def start(self):
        for i in range(self._cpus):  # create workers
            worker = Worker(self._ctx, name=str(i), tq=self.tq, rq=self.rq, init=self.worker_init)
            self.pool.append(worker)
            worker.start()
        while not all(p.is_alive() for p in self.pool):
            time.sleep(0.01)

    def execute(self, tasks: "list[Task]", tqdm=_tqdm, pbar: _tqdm=None):
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
        task_count = len(tasks)
        self._open_tasks += task_count
        task_indices = {}

        for i, t in enumerate(tasks):
            self.tq.put(t)
            task_indices[t.id] = i
        results = [None] * task_count

        if pbar is None:
            """ if pbar object was not passed, create a new tqdm compatible object """
            pbar = tqdm(total=self._open_tasks, unit='tasks')

        while self._open_tasks != 0:
            try:
                task_key, res = self.rq.get_nowait()
                self._open_tasks -= 1
                results[task_indices[task_key]] = res
                pbar.update(1)
            except queue.Empty:
                dead_processes = list(filter(lambda p: not p.is_alive() and p.exitcode != 0, self.pool))
                if len(dead_processes) > 0:
                    return_codes = [p.exitcode for p in dead_processes]
                    return_codes_str = ", ".join(str(p) for p in return_codes)

                    if -9 in return_codes:
                        raise ChildProcessError(f"One or more of processes were killed, likely because system ran out of memory. Exit codes: {return_codes_str}")
                    raise ChildProcessError(f"One or more processes exited abruptly. Exit codes: {return_codes_str}")

                time.sleep(0.01)
        return results

    def submit(self, task: Task):
        """ permits asynchronous submission of tasks. """
        if not isinstance(task, Task):
            raise TypeError(f"expected mplite.Task, not {type(task)}")
        self._open_tasks += 1
        self.tq.put(task)

    def take(self):
        """ permits asynchronous retrieval of results """
        try:
            _, result = self.rq.get_nowait()
            self._open_tasks -= 1
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
