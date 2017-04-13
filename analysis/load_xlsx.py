# -*- encoding:utf-8 -*-

import csv
import cPickle as pkl
import os
import re
from collections import defaultdict
from openpyxl import load_workbook
from functools import wraps
from pdb import set_trace as bp


def decode(s):
    try:
        return s.decode('utf-8')
    except:
        return s


def encode(s):
    try:
        return s.encode('utf-8')
    except:
        return s


def pickling(func):
    @wraps(func)
    def deco(*args, **kwargs):
        if args:
            update = args[0]
        else:
            update = kwargs.get('update', False)
        pkl_name = os.path.join('./tmp', func.func_name + '.pkl')
        if os.path.isfile(pkl_name) and not update:
            with open(pkl_name) as pkl_file:
                return pkl.load(pkl_file)
        else:
            ret = func(*args, **kwargs)
            with open(pkl_name, 'w') as pkl_file:
                pkl.dump(ret, pkl_file)
            return ret
    return deco


def preprocess(s):
    s = decode(s)
    s = re.sub(' ', '', s)
    pattern = r'\[\d{4}\-\d{2}\-\d{2}\d{2}:\d{2}:\d{2}\]'
    return re.sub(pattern, '', s)


@pickling
def read_data(update=False):
    labelname_sentence_dict = dict()
    wb = load_workbook('./data/0411_training_set.xlsx')
    for ws in wb.worksheets:
        sentences = [preprocess(cell.value)
                     for column in ws.columns
                     for cell in column
                     if cell.value is not None]
        del sentences[0]  # delete 'label'
        del sentences[0]  # delete 'sentence'
        labelname_sentence_dict[ws.title] = sentences
    wb.close()
    del wb
    return labelname_sentence_dict


@pickling
def get_label_idx_dict(update=False):
    ret = dict()
    with open('./data/label_info.csv') as label_info:
        reader = csv.reader(label_info)
        for idx, label in reader:
            ret[label] = idx
    return ret


@pickling
def get_sentence_idx_dict_and_latest_pid(update=False):
    sid = defaultdict(list)
    max_pid = -1
    with open('./data/texts_all.csv') as text_file:
        reader = csv.reader(text_file)
        for post_id, sentence_seq, sentence in reader:
            post_id = int(post_id)
            sentence_seq = int(sentence_seq)
            sid[preprocess(sentence)].append([post_id, sentence_seq])
            if post_id > max_pid:
                max_pid = post_id
    return sid, max_pid


def gen_newline(tset, lid, sid, start_pid):
    seq = 0
    for label, sentences in tset.iteritems():
        for sentence in sentences:
            if sentence not in sid:
                sentence = encode(sentence)
                text_row_exception = [start_pid, seq, sentence]
                label_row_exception = [start_pid, seq, 3, lid[label], label]
                seq += 1
                yield False, [label_row_exception, text_row_exception]
            else:
                pid_seq_list = sid[sentence]
                label_rows = []
                for pid, seq in pid_seq_list:
                    label_rows.append([pid, seq, 3, lid[label], label])
                yield True, label_rows


def store(find, rows, label_writer, text_writer):
    if find:
        label_writer.writerows(rows)
    else:
        label_writer.writerow(rows[0])
        text_writer.writerow(rows[1])


def run():
    tset = read_data()
    lid = get_label_idx_dict()
    sid, max_pid = get_sentence_idx_dict_and_latest_pid()
    with open('./data/label_new.csv', 'w') as label_file, open('./data/text_new.csv', 'w') as text_file:
        label_writer = csv.writer(label_file)
        text_writer = csv.writer(text_file)
        for find, rows in gen_newline(tset, lid, sid, max_pid+1):
            store(find, rows, label_writer, text_writer)
    del tset
    del lid
    del sid


def main():
    run()


if __name__ == '__main__':
    main()
