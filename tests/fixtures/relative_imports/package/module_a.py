"""Module A."""

from .module_b import func_b

def func_a():
    return f"A calls {func_b()}"
