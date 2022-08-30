import multiprocessing
import time
from mplite import TaskManager, Task


def run_calcs_calls(mp_enabled=True, rng=50_000_000, calls=20, cpus=1):
    start = time.perf_counter()
    L = []
    if mp_enabled:
        with TaskManager(cpu_count=cpus) as tm:
            tasks = []
            for call in range(1, calls+1):
                tasks.append(Task(fun, *(call, rng)))
            L = tm.execute(tasks)
    else:
        for call in range(1, calls+1):
            res = fun(call, rng)
            L.append(res)

    task_times = [tm for res, tm in L]
    cpu_count = cpus if mp_enabled else 1
    cpu_task_time = sum(task_times)/cpu_count

    if mp_enabled:
        print('mplite - enabled')
    else:
        print('mplite - disabled')

    print('cpu_count: ', cpu_count)
    print(f'avg. time taken per cpu: ', cpu_task_time)
    end = time.perf_counter()
    total_time = end - start
    print('total time taken: ', total_time)
    print()
    return total_time, cpu_task_time, cpu_count


def fun(call_id, rng):
    # burn some time iterating thru
    start = time.perf_counter()
    t = 0
    for i in range(rng):
        t = i/call_id
    end = time.perf_counter()
    return t, end - start


def run_calcs_sleep(mp_enabled, sleep=2, cpus=1):
    args = list(range(20))
    start = time.perf_counter()
    prev_mem = 0
    L = []

    if mp_enabled:
        with TaskManager(cpus) as tm:
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

    end = time.perf_counter()

    cpu_count = cpus if mp_enabled else 1

    if mp_enabled:
        print('mplite - enabled')
    else:
        print('mplite - disabled')

    total_time = end - start
    print('cpu_count: ', cpu_count)
    print('total time taken: ', total_time)
    print()
    return total_time, cpu_count


def adder(a, b, sleep):
    time.sleep(sleep)
    return a+b


def test_mplite_performance():
    # change calls and range to see the knock on effect on performance
    print('========CALLS TEST===========')
    for cpus in [1, multiprocessing.cpu_count()]:
        for ix, (calls, rng) in enumerate([(10, 50_000_000), (2000, 50)], start=1):
            print('calls: ', calls, ', range: ', rng)
            total_time_mp_e, cpu_task_time_mp_e, cpu_count_mp_e = run_calcs_calls(True, rng, calls, cpus)
            total_time_mp_d, cpu_task_time_mp_d, cpu_count_mp_d = run_calcs_calls(False, rng, calls, cpus)
            artifacts = [cpus, calls, rng, total_time_mp_e, cpu_task_time_mp_e, cpu_count_mp_e, total_time_mp_d, cpu_task_time_mp_d, cpu_count_mp_d]
            if cpu_count_mp_e > cpu_count_mp_d:
                if ix == 1: # assert mplite is faster for less calls and heavier process
                    assert total_time_mp_e < total_time_mp_d, artifacts
            else:
                assert True


    for _ in range(3):
        print()

    # change sleep times to see the knock on effect on performance
    print('========SLEEP TEST===========')
    for cpus in [1, multiprocessing.cpu_count()]:
        for ix, sleep in enumerate([2, 0.02, 0.01], start=1):
            print('sleep timer value: ', sleep)
            total_time_mp_e, cpu_count_mp_e = run_calcs_sleep(True, sleep, cpus)
            total_time_mp_d, cpu_count_mp_d = run_calcs_sleep(False, sleep, cpus)
            artifacts = [cpus, total_time_mp_e, cpu_count_mp_e, total_time_mp_d, cpu_count_mp_d]
            if cpu_count_mp_e > cpu_count_mp_d:
                if ix == 1:  # assert mplite is faster for longer sleep
                    assert total_time_mp_e < total_time_mp_d, artifacts
            else:
                assert True



