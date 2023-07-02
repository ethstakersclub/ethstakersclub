import sys
import datetime


ANSI_RESET = '\033[0m'
ANSI_GREEN = '\033[32m'
ANSI_YELLOW = '\033[33m'
ANSI_RED = '\033[31m'


def print_status(severity, message):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    severity_colors = {
        'info': ANSI_GREEN,
        'warning': ANSI_YELLOW,
        'error': ANSI_RED
    }
    severity_color = severity_colors.get(severity.lower(), '')
    formatted_message = f"[{now}] {severity_color}{severity.upper()}:{ANSI_RESET} {message}"
    sys.stdout.write(formatted_message + '\n')
    sys.stdout.flush()