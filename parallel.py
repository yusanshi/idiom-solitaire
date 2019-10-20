import math
from multiprocessing import Process, Queue
from config import WORKER_NUM


def divide_list(list_to_divide, n_part):
    length = len(list_to_divide)
    size = math.ceil(length / n_part)
    return [list_to_divide[i:i + size] for i in [i * size for i in range(n_part)]]


def worker(input, output):
    for func, args in iter(input.get, 'STOP'):
        output.put(func(*args))


def multiprocess_calc(current, graph, calc_set_all, worker_type, worker_level, one_only=False):
    TASK = [(worker_type, (worker_level, current, graph, part, one_only))
            for part in divide_list(calc_set_all, WORKER_NUM)]
    task_queue = Queue()
    done_queue = Queue()
    for task in TASK:
        task_queue.put(task)

    all_process = []
    for _ in range(WORKER_NUM):
        all_process.append(
            Process(target=worker, args=(task_queue, done_queue)))

    for p in all_process:
        p.start()

    result = []
    for _ in range(WORKER_NUM):
        result += done_queue.get()
        if one_only and len(result) != 0:
            for p in all_process:
                p.terminate()
                p.join()

            return result

    for _ in range(WORKER_NUM):
        task_queue.put('STOP')

    return result
