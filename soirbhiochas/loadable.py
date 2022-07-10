class Loadable:
    @property
    def loader(self):
        return _global_loadables

_global_loadables = {}

def add_loadable(key, path):
    _global_loadables[key] = path
