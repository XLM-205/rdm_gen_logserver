from datetime import datetime

from server_config import defaults, logger_config


def print_verbose(sender: str, message: str, color: str = None, bold: bool = False, underline: bool = False):
    """
    # Prints a message on the console if 'logger_config["VERBOSE"]' is True
    :param sender: The module that sent the message. If it matches any entry on 'defaults["INTERFACE"]["CONSOLE"]' this
    message will have that defined color. If not, it will use 'printer_color'
    :param message: The message to be printer on the console
    :param color: A color to override the default one. Needs to be a valid color of 'print_rich'. Default is None
    :param bold: If true, prints the message in bold. Default is False
    :param underline: If true, prints the message with an underline. Default is False
    """
    if sender is None:  # Abort
        return
    sender = sender.upper()
    if logger_config["VERBOSE"]:
        printer_color = None
        if color is not None:
            printer_color = color
        elif sender in defaults["INTERFACE"]["CONSOLE"]:
            printer_color = defaults["INTERFACE"]["CONSOLE"][sender]
        print_rich(f"[{datetime.now().strftime('%H:%M:%S.%f')}][{sender}] {message}",
                   color=printer_color, bold=bold, underline=underline)


def print_rich(message: str, color=None, bold=False, underline=False):
    """
    Prints text with color, header, bold or underline
    :param message: The message to be written
    :param color: 'black', 'red', 'green', 'yellow', 'blue', 'pink', 'cyan', or 'white'. Defaults to '' (none color)
    :param bold: Boolean
    :param underline: Boolean
    """
    # From https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal
    end = '\033[0m'
    b = '\033[1m' if bold else ''
    u = '\033[4m' if underline else ''
    palette = {'black': '\033[90m', 'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m', 'blue': '\033[94m',
               'pink': '\033[95m', 'cyan': '\033[96m', 'white': '\033[97m', }
    c = ''
    if color is None:
        color = ''
    else:
        color = str.lower(color)
    if color in palette:
        c = palette[color]

    print(f"{c}{b}{u}{message}{end}")
