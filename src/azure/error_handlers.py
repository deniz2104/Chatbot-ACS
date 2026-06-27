from contextlib import contextmanager

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError


@contextmanager
def resource_not_found():
    try:
        yield
    except ResourceNotFoundError:
        pass


@contextmanager
def resource_exists():
    try:
        yield
    except ResourceExistsError:
        pass
