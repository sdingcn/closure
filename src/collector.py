def collect(store, stack):
    visited = set()

    def mark(location):
        visited.add(location)
        if type(store[location]) == Closure:
            for var, loc in store[location].env:
                if loc not in visited:
                    mark(loc)

    def sweep():
        to_remove = set()
        for k, v in store.items():
            if k not in visited:
                to_remove.add(k)
        for k in to_remove:
            del store[k]

    for frame in stack:
        for var, loc in frame.env:
            mark(loc)
    n = sweep()
    sys.stderr.write('GC: collected {} locations\n'.format(n))
