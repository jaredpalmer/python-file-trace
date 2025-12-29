"""Entry module with relative imports."""
from . import helper
from ..utils import common

def run():
    helper.do_something()
    common.shared_func()
