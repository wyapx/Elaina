from logging import StreamHandler, LogRecord

_color_mapper = {
    0: "\33[34m",
    10: "\33[35m",
    20: "\33[32m",
    30: "\33[33m",
    40: "\33[31m",
    50: "\33[30m"
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
