# -*- encoding: utf-8 -*-
import os
import csv
import sys
import logging
import logging.handlers
from functools import wraps
from StringIO import StringIO
from time import time
from pdb import set_trace
reload(sys)
sys.setdefaultencoding('utf-8')


class Utils(object):
    @staticmethod
    def human_readable_time_string(s):
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return '%d h %02d m %02d s' % (h, m, s)

    @staticmethod
    def file_length(filename):
        if os.path.isfile(filename):
            with open(filename) as f:
                return len(f.readlines())
        else:
            return -1

    @staticmethod
    def change_ext(filename, ext):
        fname, _ = os.path.splitext(filename)
        return '%s.%s' % (fname, ext)

    @staticmethod
    def iter_csv(path, nth=None, delimiter=','):
        with open(path) as f:
            csv_reader = csv.reader(f, delimiter=delimiter)
            for row in csv_reader:
                if nth:
                    yield row[nth]
                else:
                    yield row

    @staticmethod
    def list_to_csv(l):
        sio = StringIO()
        csv_writer = csv.writer(sio)
        csv_writer.writerow(l)
        csv_string = sio.getvalue().strip()
        return csv_string

    @staticmethod
    def process(func):
        @wraps(func)
        def with_process(*args, **kwargs):
            sys.stdout.write('{:<50s}[ ]\r'.format(func.__name__))
            sys.stdout.flush()
            start_time = time()
            result = func(*args, **kwargs)
            time_taken = Utils.human_readable_time_string(time() - start_time)
            sys.stdout.write('{:<50s}[v] {time_taken}\n'.format(func.__name__, time_taken=time_taken))
            return result
        return with_process

    @staticmethod
    def logger(name, logfile, level=0, stream=False):
        logger = logging.getLogger(name)
        parent = logger
        while parent:
            parent.setLevel(level)
            parent = parent.parent
        formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
        # file handler
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        # stream handler
        if stream:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
        # binding
        return logger


class Progress(object):
    def __init__(self, obj, length, update_interval=None):
        self.iterable = iter(obj)
        self.length = length
        self.interval = update_interval or length/200
        self.idx = 0
        self.std = sys.stdout

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.update()
            self.idx += 1
            return self.iterable.next()
        except:
            self.finish()
            raise

    next = __next__

    def get_bar(self):
        return '{:<100s}'.format('#' * (100 * self.idx / self.length))

    def get_percent(self):
        return '{:>5f}%'.format(100. * self.idx / self.length)

    def get_ratio(self):
        format_string = '{:>%dd}' % len(str(self.length))
        return '{f}/{f}'.format(f=format_string).format(self.idx, self.length)

    def update(self):
        if self.idx % self.interval != 0:
            return
        self.std.write('[{bar}]({ratio}, {percent})\r'
                       .format(bar=self.get_bar(),
                               ratio=self.get_ratio(),
                               percent=self.get_percent()))
        self.std.seek(0)
        self.std.truncate(0)

    def finish(self):
        self.std.write('\n')
        self.std.flush()
