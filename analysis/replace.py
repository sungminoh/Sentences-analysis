# -*- coding: utf-8 -*-
import re
import csv
import argparse
from helpers import Utils, Progress


class Replacer(object):
    PHONE = '(\+\d{1,2}\s)?\(?\d{2,3}\)?[\s.-]\d{3,4}[\s.-]\d{4}'
    PHONE_REPLACEMENT = ' __PHONE__ '
    URL = u'http[s]?:(?:\s?/)/(?:[a-zA-Z]|[0-9]|(?:\s?[$-_@.&+])|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F])|[…])+'
    INVALID = 'í ½'

    URL_REPLACEMENT = u' __URL__ '

    def __init__(self, filename, nth=-1):
        self.filename = filename
        self.logger = Utils.logger(self.__class__.__name__, './replace.log')
        self.nth = nth

    @staticmethod
    def replace_phone(string):
        try:
            return re.sub(Replacer.PHONE, Replacer.PHONE_REPLACEMENT, string)
        except BaseException as e:
            print e
            return string

    @staticmethod
    def replace_url(string):
        try:
            string = string.decode('utf-8')  # to unicode
            ret = re.sub(Replacer.URL, Replacer.URL_REPLACEMENT, string, flags=re.UNICODE)
            return ret.encode('utf-8')  # to askii
        except BaseException as e:
            print e
            return string

    def __is_valid(self, string):
        return Replacer.INVALID not in string

    def gen_replace_all(self):
        replaced_pattern = '%s|%s' % (self.PHONE_REPLACEMENT, self.URL_REPLACEMENT)
        for row in Utils.iter_csv(self.filename):
            sentence = row[self.nth]
            if not self.__is_valid(sentence):
                continue
            replaced = Replacer.replace_url(Replacer.replace_phone(sentence))
            row[self.nth] = replaced
            if bool(re.search(replaced_pattern, row[self.nth])):
                self.logger.info('%s -> %s' % (sentence.decode('utf-8'), replaced.decode('utf-8')))
            yield row

    @Utils.process
    def extract_output(self, out_filename):
        with open(out_filename, 'w') as f:
            csv_writer = csv.writer(f, delimiter=',')
            for row in Progress(self.gen_replace_all(), Utils.file_length(self.filename), 10):
                csv_writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description='replace phone numbers and urls.')
    parser.add_argument('--input', '-in', default='./data/texts_all.csv', help='input text.csv.file')
    parser.add_argument('--output', '-out', default='./data/texts_all_replaced.csv', help='output file path')
    args = parser.parse_args()
    Replacer(args.input).extract_output(args.output)


if __name__ == '__main__':
    main()
