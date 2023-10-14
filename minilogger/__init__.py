try:
    from colorama import Fore, Back, Style
except:
    class Empty: ...
    Fore = Empty()
    Fore.RED = ''
    Fore.YELLOW = ''
    Fore.LIGHTBLACK_EX = ''
    Back = Empty()
    Back.RED = ''
    Style = Empty()
    Style.RESET_ALL = ''

scheme = {
    'F': {
        'description': 'FATAL',
        'level': 0,
        'fore': '',
        'back': Back.RED
    },
    'E': {
        'description': 'ERROR',
        'level': 1,
        'fore': Fore.RED,
        'back': ''
    },
    'W': {
        'description': 'WARN',
        'level': 2,
        'fore': Fore.YELLOW,
        'back': ''
    },
    'I': {
        'description': 'INFO',
        'level': 3,
        'fore': '',
        'back': ''
    },
    'D': {
        'description': 'DEBUG',
        'level': 4,
        'fore': Fore.LIGHTBLACK_EX,
        'back': ''
    }
}

class Console:
    level = 'D'

    @classmethod
    def log(self, message: str, source: str = 'main', level: str = 'I'):
        level = level.upper()

        if scheme[self.level.upper()]['level'] < scheme[level]['level']:
            return None

        print(f'{scheme[level]["fore"]}{scheme[level]["back"]}{scheme[level]["description"]}{Style.RESET_ALL} \t{scheme[level]["fore"]}{scheme[level]["back"]}{source}{Style.RESET_ALL} \t{scheme[level]["fore"]}{scheme[level]["back"]}{message}{Style.RESET_ALL}')

print()

if __name__ == '__main__':
    Console.log('first test message', 'minilogger', 'D')
    Console.log('second test message', 'minilogger', 'I')
    Console.log('third test message', 'minilogger', 'W')
    Console.log('fourth test message', 'minilogger', 'E')
    Console.log('fifth test message', 'minilogger', 'F')