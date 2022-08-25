import time
from mplite import TaskManager, Task


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

    count = end - start
    print('time taken: ', count)
    print(L)
    return count


def fun(call_id, rng):
    # burn some time iterating thru
    t = 0
    for i in range(rng):
        t = i/call_id
    return t


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

    count = end - start
    print('time taken: ', count)
    print(L)
    return count


def adder(a, b, sleep):
    time.sleep(sleep)
    return a+b


def test_mplite_performance():
    # change calls and range to see the knock on effect on performance
    print('========CALLS TEST===========')
    calls = 10 # number of calls
    rng = 50_000_000 # iterations in the call to spend some time calculating
    print('calls: ', calls, ', range: ', rng)
    mp_e = run_calcs_calls(True, rng, calls)
    mp_d = run_calcs_calls(False, rng, calls)
    assert mp_e < mp_d
    print()
    calls = 2000 # number of calls
    rng = 50 # iterations in the call to spend some time calculating
    print('calls: ', calls, ', range: ', rng)
    mp_e = run_calcs_calls(True, rng, calls)
    mp_d = run_calcs_calls(False, rng, calls)
    assert mp_e > mp_d

    for i in range(3):
        print()

    # change sleep times to see the knock on effect on performance
    print('========SLEEP TEST===========')
    sleep = 2
    print('sleep timer value: ', sleep)
    mp_e = run_calcs_sleep(True, sleep)
    mp_d = run_calcs_sleep(False, sleep)
    assert mp_e < mp_d
    print()
    sleep = 0.02
    print('sleep timer value: ', sleep)
    mp_e = run_calcs_sleep(True, sleep)
    mp_d = run_calcs_sleep(False, sleep)
    assert mp_e > mp_d
    sleep = 0.01
    print('sleep timer value: ', sleep)
    mp_e = run_calcs_sleep(True, sleep)
    mp_d = run_calcs_sleep(False, sleep)
    assert mp_e > mp_d

