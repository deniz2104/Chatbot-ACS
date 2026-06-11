from typing import Callable

_registry: list[Callable] = []


def register(fn: Callable) -> None:
    _registry.append(fn)

def make_singleton(factory: Callable, on_shutdown: Callable | None = None):
    instance = [None]

    def get():
        if instance[0] is None:
            instance[0] = factory()
        return instance[0]

    def shutdown():
        if on_shutdown is not None and instance[0] is not None:
            on_shutdown(instance[0])
        instance[0] = None

    _registry.append(shutdown)
    return get
