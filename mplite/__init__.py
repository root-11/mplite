import io
import sys
import multiprocessing
import traceback
import time
from tqdm import tqdm as _tqdm
import queue
from itertools import count
from typing import Callable, Any, Union, Tuple, Literal
from multiprocessing.context import BaseContext
import tblib.pickling_support as pklex

major, minor, patch = 1, 3, 0
__version_info__ = (major, minor, patch)
__version__ = '.'.join(str(i) for i in __version_info__)
default_context = "spawn"

ERR_MODE_STR = "str"
ERR_MODE_EXCEPTION = "exception"


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
        return repr(self)

    def __repr__(self) -> str:
        return f"Task(f={self.f.__name__}, *{self.args}, **{self.kwargs})"

    def execute(self):
        return self.f(*self.args, **self.kwargs)


class TaskChain(object):
    def __init__(self, task: Task, next_task: Callable[[Task, Any], Union[Task, "TaskChain"]] = None) -> None:
        """
            allows for promise-like chain execution of tasks, where one task depends on the output of another
            only supported by TaskManager.execute API, submit/take would have to be implemented manually

            reasoning: sometimes you want multiple steps of tasks executed,
            however, when using .execute API the system would wait for results in a blocking manner
            this API allows you to create a new task that gets queued automatically once the parent task is ready,
            this allows for each of the steps to be executed in a non-blocking manner
        """
        self.id = next(Task.task_id_counter)
        self.task = task
        self.next = next_task

        self.task.id = self.id

    def resolve(self, result):
        """ called by task manager, when TaskChain is executed, if not last task, create a new task and shove it into task queue """
        if self.next is not None:
            task = self.next(self.task, result)
            task.id = self.id

            if isinstance(task, TaskChain):
                task.task.id = self.id

            return task
        raise StopIteration()

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f"TaskChain(f={self.task.f.__name__}, *{self.task.args}, **{self.task.kwargs}, is_last={self.next is None})"

    def execute(self):
        """ execute task chain synchronously """
        t = self

        while True:
            if isinstance(t, TaskChain):
                t = t.resolve(t.task.execute())
            elif isinstance(t, Task):
                return t.execute()
            else:
                raise Exception("invalid type")


class Worker(object):
    def __init__(self, ctx: BaseContext, name: str, tq: multiprocessing.Queue, rq: multiprocessing.Queue, init: Task, error_mode: Literal["str", "exception"]):
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
        error_mode: 'str' | 'exception'
            Which error mode to use, 'str' for legacy where exception is returned as string or 'exception' where exception is returned as pickled object.
        """
        assert error_mode in (ERR_MODE_STR, ERR_MODE_EXCEPTION), f"Error mode must be in ('{ERR_MODE_STR}', '{ERR_MODE_EXCEPTION}'), got '{error_mode}'"
        self.ctx = ctx
        self.exit = ctx.Event()
        self.tq = tq  # workers task queue
        self.rq = rq  # workers result queue
        self.init = init

        self.err_mode = error_mode
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

        do_task = _do_task_exception_mode if self.err_mode == ERR_MODE_EXCEPTION else _do_task_str_mode

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
                self.rq.put((task.id, do_task(task)))
            else:
                time.sleep(0.01)


class TaskManager(object):
    def __init__(self, cpu_count: int = None, context=default_context, worker_init: Task = None, error_mode: Literal["str", "exception"] = ERR_MODE_STR) -> None:
        """
        Class responsible for managing worker processes and tasks.

        OPTIONAL
        --------
        cpu_count: int
            Number of worker processes to use.
            Default: {cpu core count}.
        ctx: BaseContext
            Process spawning context ForkContext/SpawnContext. Note: Windows cannot fork.
            Default: "spawn"
        worker_init: Task | None
            Task executed when worker starts.
            Default: None
        error_mode: 'str' | 'exception'
            Which error mode to use, 'str' for legacy where exception is returned as string or 'exception' where exception is returned as pickled object.
            Default: 'str'
        """

        assert error_mode in (ERR_MODE_STR, ERR_MODE_EXCEPTION), f"Error mode must be in ('{ERR_MODE_STR}', '{ERR_MODE_EXCEPTION}'), got '{error_mode}'"
        assert worker_init is None or isinstance(worker_init, Task), "Init is not (None, type[Task])"

        self._ctx = multiprocessing.get_context(context)
        self._cpus = multiprocessing.cpu_count() if cpu_count is None else cpu_count
        self.tq = self._ctx.Queue()
        self.rq = self._ctx.Queue()
        self.pool: list[Worker] = []
        self._open_tasks: list[int] = []

        self.error_mode = error_mode
        self.worker_init = worker_init

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # signature requires these, though I don't use them.
        self.stop()  # stop the workers.

    def start(self):
        for i in range(self._cpus):  # create workers
            worker = Worker(self._ctx, name=str(i), tq=self.tq, rq=self.rq, init=self.worker_init, error_mode=self.error_mode)
            self.pool.append(worker)
            worker.start()
        while not all(p.is_alive() for p in self.pool):
            time.sleep(0.01)

    def execute(self, tasks: "list[Union[Task, TaskChain]]", tqdm=_tqdm, pbar: _tqdm = None):
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
        tasks_running = [t.id for t in tasks]
        self._open_tasks.extend(tasks_running)
        task_indices: dict[int, Tuple[int, Union[Task, TaskChain]]] = {}

        for i, t in enumerate(tasks):
            self.tq.put(t if isinstance(t, Task) else t.task)
            task_indices[t.id] = (i, t)
        results = [None] * task_count

        if pbar is None:
            """ if pbar object was not passed, create a new tqdm compatible object """
            pbar = tqdm(total=task_count, unit='tasks')

        while len(tasks_running) > 0:
            try:
                task_key, (success, res) = self.rq.get_nowait()

                if not success and self.error_mode == ERR_MODE_EXCEPTION:
                    [self._open_tasks.remove(idx) for idx in tasks_running]
                    raise unpickle_exception(res)

                idx, t = task_indices[task_key]
                if isinstance(t, Task) or t.next is None:
                    self._open_tasks.remove(t.id)
                    tasks_running.remove(t.id)
                    results[idx] = res
                    pbar.update(1)
                else:
                    t = t.resolve(res)
                    task_indices[task_key] = (idx, t)
                    self.tq.put(t if isinstance(t, Task) else t.task)
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
        self._open_tasks.append(task.id)
        self.tq.put(task)

    def take(self):
        """ permits asynchronous retrieval of results """
        try:
            task_id, (success, result) = self.rq.get_nowait()

            self._open_tasks.remove(task_id)

            if not success and self.error_mode == ERR_MODE_EXCEPTION:
                raise unpickle_exception(result)

        except queue.Empty:
            result = None
        return result

    @property
    def open_tasks(self):
        return len(self._open_tasks)

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


def pickle_exception(e: Exception):
    print(e)
    if e.__traceback__ is not None:
        tback = pklex.pickle_traceback(e.__traceback__)
        e.__traceback__ = None
    else:
        tback = None

    pkld = pklex.pickle_exception(e)
    print(pkld)
    fn_ex, (ex_cls, ex_txt, ex_rsn, _) = pkld

    return fn_ex, (ex_cls, ex_txt, ex_rsn, tback)


def unpickle_exception(e):
    fn_ex, (ex_cls, ex_txt, ex_rsn, tback) = e

    if tback is not None:
        fn_tback, args_tback = tback
        tback = fn_tback(*args_tback)

    return fn_ex(ex_cls, ex_txt, ex_rsn, tback)


def _do_task_exception_mode(task: Task):
    """ execute task in exception mode"""
    try:
        return True, task.execute()
    except Exception as e:
        return False, pickle_exception(e)


def _do_task_str_mode(task: Task):
    """ execute task in legacy string mode """
    try:
        return True, task.execute()
    except Exception:
        f = io.StringIO()
        traceback.print_exc(limit=3, file=f)
        f.seek(0)
        error = f.read()
        f.close()

        return False, error
