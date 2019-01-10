import six
from io import StringIO


def decode_text(text):
    decoders = ["utf-8", "Windows-1252"]
    for decoder in decoders:
        try:
            return text.decode(decoder)
        except UnicodeDecodeError:
            continue
    return text.decode("utf-8", "ignore")  # Ignore not compatible characters


class MockOutput(object):
    """ wraps an output stream, so it can be pretty colored,
    and auxiliary info, success, warn methods for convenience.
    """

    def __init__(self):
        self._stream = StringIO()

    def __repr__(self):
        if six.PY2:
            return str(self._stream.getvalue().encode("ascii", "ignore"))
        else:
            return self._stream.getvalue()

    def __str__(self, *args, **kwargs):
        return self.__repr__()

    def __eq__(self, value):
        return self.__repr__() == value

    def __ne__(self, value):
        return not self.__eq__(value)

    def __contains__(self, value):
        return value in self.__repr__()

    @property
    def is_terminal(self):
        return hasattr(self._stream, "isatty") and self._stream.isatty()

    def writeln(self, data, front=None, back=None):
        self.write(data, front, back, True)

    def write(self, data, front=None, back=None, newline=False):  # Should keep same interface
        if six.PY2:
            if isinstance(data, str):
                data = decode_text(data)  # Keep python 2 compatibility

        if newline:
            data = "%s\n" % data

        try:
            self._stream.write(data)
        except UnicodeError:
            data = data.encode("utf8").decode("ascii", "ignore")
            self._stream.write(data)
        self.flush()

    def info(self, data):
        self.writeln(data)

    def highlight(self, data):
        self.writeln(data)

    def success(self, data):
        self.writeln(data)

    def warn(self, data):
        self.writeln("WARN: " + data)

    def error(self, data):
        self.writeln("ERROR: " + data)

    def input_text(self, data):
        self.write(data)

    def rewrite_line(self, line):
        TOTAL_SIZE = 70
        LIMIT_SIZE = 32  # Hard coded instead of TOTAL_SIZE/2-3 that fails in Py3 float division
        if len(line) > TOTAL_SIZE:
            line = line[0:LIMIT_SIZE] + " ... " + line[-LIMIT_SIZE:]
        self.write("\r%s%s" % (line, " " * (TOTAL_SIZE - len(line))))
        self._stream.flush()

    def flush(self):
        self._stream.flush()
