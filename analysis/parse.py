# -*- coding: utf-8 -*-
import argparse
import csv
import click
from konlpy.tag import Twitter
from helpers import Utils, Progress


class ParseUtils(Utils):
    @staticmethod
    def concat_tuple(tup):
        assert isinstance(tup, tuple)
        return '_'.join(tup)


class Parser(object):
    def __init__(self, filename=None, nth=-1):
        self.filename = filename
        self.nth = nth
        self.twitter = Twitter()
        self.logger = ParseUtils.logger(self.__class__.__name__, './parse.log')

    def parse_sentence(self, sentence):
        return self.twitter.pos(sentence)

    def parse_all_generator(self, filename=None, nth=None):
        if filename is None:
            filename = self.filename or click.prompt('file name is required')
        if nth is None:
            nth = self.nth
        for row in ParseUtils.iter_csv(filename):
            try:
                parsed = self.parse_sentence(row[nth])
                concated = ' '.join([ParseUtils.concat_tuple(x) for x in parsed])
                row[nth] = concated
            except BaseException as e:
                msg = '{error:<80}  |  {data}'.format(error=str(e), data=ParseUtils.list_to_csv(row))
                self.logger.error(msg)
                continue
            yield row

    def extract_parsed(self, out_filename, filename=None, nth=None):
        if filename is None:
            filename = self.filename or click.prompt('file name is required')
        filelength = ParseUtils.file_length(filename)
        if nth is None:
            nth = self.nth
        with open(out_filename, 'w') as f:
            csv_writer = csv.writer(f)
            for row in Progress(self.parse_all_generator(), filelength, 10):
                csv_writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description='parse texts.')
    parser.add_argument('--input', '-in', default='./data/texts_all_replaced.csv', help='input text.csv.file')
    parser.add_argument('--output', '-out', default='./data/texts_all_parsed.csv', help='output file path')
    args = parser.parse_args()
    Parser(args.input, nth=-1).extract_parsed(args.output)


if __name__ == '__main__':
    main()
