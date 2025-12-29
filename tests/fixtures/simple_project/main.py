"""Main entry point for the simple project."""

from utils import helper_function
from models import User

def main():
    user = User("test")
    result = helper_function(user.name)
    print(result)

if __name__ == "__main__":
    main()
