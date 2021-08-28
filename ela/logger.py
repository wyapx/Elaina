import os
import sys
from logging import StreamHandler, LogRecord

_color_mapper = {
    0: "\33[34m",
    10: "\33[35m",
    20: "\33[32m",
    30: "\33[33m",
    40: "\33[31m",
    50: "\33[30m"
}


# https://github.com/django/django/blob/main/django/core/management/color.py
def supports_color() -> bool:
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
