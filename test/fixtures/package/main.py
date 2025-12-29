"""Test case with package imports."""
import mypackage
from mypackage import module_a
from mypackage.module_b import func_b

def main():
    mypackage.greet()
    module_a.func_a()
    func_b()

if __name__ == "__main__":
    main()
