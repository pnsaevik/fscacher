def dump_pickle(obj, fname):
    import pickle
    with open(fname, 'bw') as f:
        pickle.dump(obj, f, protocol=4)


def load_pickle(fname):
    import pickle
    with open(fname, 'br') as f:
        return pickle.load(f)
