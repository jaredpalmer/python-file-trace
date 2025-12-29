"""Test case with dynamic imports."""
import importlib

# Dynamic import using __import__
mod1 = __import__('static_module')

# Dynamic import using importlib
mod2 = importlib.import_module('another_module')

# Non-static dynamic import (should produce warning)
module_name = 'dynamic_name'
mod3 = importlib.import_module(module_name)

def main():
    mod1.func1()
    mod2.func2()

if __name__ == "__main__":
    main()
