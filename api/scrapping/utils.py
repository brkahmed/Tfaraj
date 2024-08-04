import logging
import sys
from colorama import init, Fore, Style

init(autoreset=True)

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler for all log levels
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # File handler for warning and higher levels
    file_handler = logging.FileHandler(name + '.log')
    file_handler.setLevel(logging.WARNING)

    # Log format
    formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')

    # Adding formatter to handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Adding handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Define colors for different log levels
    colors = {
        name: '\033[38;5;208m',
        'DEBUG': Fore.BLUE + Style.BRIGHT,
        'INFO': Fore.GREEN + Style.BRIGHT,
        'WARNING': Fore.YELLOW + Style.BRIGHT,
        'ERROR': Fore.RED + Style.BRIGHT,
        'CRITICAL': Fore.RED + Style.BRIGHT + Style.BRIGHT,
    }

    # Custom log filter to add colors
    class CustomFilter(logging.Filter):
        def filter(self, record):
            record.levelname = colors[record.levelname] + record.levelname + Style.RESET_ALL
            record.name = colors[record.name] + record.name + Style.RESET_ALL

            return True

    console_handler.addFilter(CustomFilter())

    return logger
