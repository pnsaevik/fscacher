import json
from uuid import uuid4


def timestwo(i):
    return i * 2


def jsondump(*args):
    fname = uuid4().hex

    with open(fname, 'w') as f:
        json.dump(list(args), f)

    return fname
