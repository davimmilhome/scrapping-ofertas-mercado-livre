from enum import Enum

class TypeOfDriver(Enum):
    FIREFOX = 'FIREFOX'
    CHROME = 'CHROME'


if __name__ == '__main__':
    print(TypeOfDriver.CHROME)