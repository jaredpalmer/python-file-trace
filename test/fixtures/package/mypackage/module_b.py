"""Module B."""
from . import module_a

def func_b():
    module_a.func_a()
    print("Function B")
