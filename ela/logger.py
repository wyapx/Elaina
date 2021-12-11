import logging
import os
import sys
from logging import StreamHandler, LogRecord
from typing import Optional, List

_color_mapper = {
    0: "\33[34m",  # NOTSET blue
    10: "\33[35m",  # DEBUG purple
    20: "\33[32m",  # INFO green
    30: "\33[33m",  # WARN yellow
    40: "\33[31m",  # ERROR red
    50: "\33[36m"  # CRITICAL white
}


class ColoredStreamHandler(StreamHandler):
    terminator = "\33[0m\n"

    def emit(self, record: LogRecord) -> None:
        try:
            msg = self.format(record)
            stream = self.stream
            # issue 35046: merged two stream.writes into one.
            stream.write(_color_mapper.get(record.levelno, "\33[36m") + msg + self.terminator)
            self.flush()
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)


# https://github.com/django/django/blob/main/django/core/management/color.py
def supported_color() -> bool:
    """
    Return True if the running system's terminal supports color,
    and False otherwise.
    """

    def vt_codes_enabled_in_windows_registry():
        """
        Check the Windows Registry to see if VT code handling has been enabled
        by default, see https://superuser.com/a/1300251/447564.
        """
        try:
            # winreg is only available on Windows.
            import winreg
        except ImportError:
            return False
        else:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Console')
            try:
                reg_key_value, _ = winreg.QueryValueEx(reg_key, 'VirtualTerminalLevel')
            except FileNotFoundError:
                return False
            else:
                return reg_key_value == 1

    # Pycharm console support ansi color log
    if "PYCHARM_HOSTED" in os.environ:
        return True
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    return is_a_tty and (
            sys.platform != 'win32' or
            'ANSICON' in os.environ or
            # Windows Terminal supports VT codes.
            'WT_SESSION' in os.environ or
            # Microsoft Visual Studio Code's built-in terminal supports colors.
            os.environ.get('TERM_PROGRAM') == 'vscode' or
            vt_codes_enabled_in_windows_registry()
    )


def initial_logger(
        level=logging.INFO,
        enable_log_color=True,
        log_fmt: str = None,
        datefmt: Optional[str] = None,
        handlers: List[logging.Handler] = None
):
    if handlers is None:
        handlers = []
    if log_fmt is None:
        log_fmt = "%(asctime)s %(name)s[%(levelname)s] -> %(message)s"
    if enable_log_color and supported_color():
        handlers.append(ColoredStreamHandler())
    elif not handlers:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=level, handlers=handlers, datefmt=datefmt, format=log_fmt)
