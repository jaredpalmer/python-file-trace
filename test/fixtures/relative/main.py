"""Test case with relative imports."""
from subpkg import entry

def main():
    entry.run()

if __name__ == "__main__":
    main()
