import json
from uuid import uuid4


_COUNTER = [0]


def timestwo(i):
    return i * 2


def jsondump(*args):
    fname = uuid4().hex

    with open(fname, 'w') as f:
        json.dump(list(args), f)

    return fname


def increment():
    _COUNTER[0] += 1
    return jsondump(_COUNTER[0])


def reset_counter():
    _COUNTER[0] = 0
    return jsondump(0)
