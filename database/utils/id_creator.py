import time
import random
import string

class IDCreator:

    @staticmethod
    def get_new_id(number_of_digits, letter_on=False):

        counter = 1
        timestamp = int(time.time() * 1000)  # Get current time in milliseconds
        new_id = (timestamp << 16) | (counter & 0xFFFF)  # Combine timestamp and counter
        id_str = str(new_id)[-number_of_digits:]

        if letter_on:
            number_of_letters = (number_of_digits // 2) - 1
            if number_of_digits % 2 != 0:
                number_of_letters = ((number_of_digits + 1) // 2) - 2


            letters = ''.join(random.choices(string.ascii_uppercase, k=number_of_letters))
            id_str = id_str[:number_of_digits - number_of_letters] + letters

        return id_str

if __name__ == '__main__':
    idc = IDCreator()
    print(idc.get_new_id(7, True))