# -*- coding: utf-8 -*-
import os
import sys
import csv
from collections import defaultdict
import click
import MySQLdb as mdb
import imp
database_info = imp.load_source('database_info', '../database_info.py')
mysql_info = database_info.mysql_info()


def iter_csv(path):
    with open(path) as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            yield row


def build_post_category_dic(it):
    dic = defaultdict(dict)
    for row in it:
        post_id, sentence_seq = row[:2]
        categories = row[2].split()
        dic[post_id][sentence_seq] = categories
    return dic


def argmax(lst):
    x = []
    m = -1
    for i, e in enumerate(lst):
        if e == m:
            x.append(i)
        elif e > m:
            m = e
            del x[:]
            x.append(i)
    return x


def build_lda_result_dic(it, post_category_dic):
    dic = defaultdict(list)
    for row in it:
        post_id, sentence_seq = row[0:2]
        posibility_vector = row[2].split()
        categories = post_category_dic[post_id][sentence_seq]
        top_indices = argmax(posibility_vector)
        for i in top_indices:
            dic[i].append((post_id, sentence_seq, categories))
    return dic


def retrieve_full_sentence(lda_result_dic, fname):
    f = open(fname, 'w')
    csv_writer = csv.writer(f, delimiter=',')
    with click.progressbar(lda_result_dic.keys(), label='retrieving sentences') as bar:
        for i in bar:
            db = mdb.connect(**mysql_info)
            cur = db.cursor()
            for post_id, sentence_seq, categories in lda_result_dic[i]:
                query = """
                        select full_text from sentences where post_id = %s and sentence_seq = %s
                        """ % (post_id, sentence_seq)
                cur.execute(query)
                text = cur.fetchall()[0][0].encode('utf-8')
                csv_line = [i, post_id, sentence_seq,
                            ' '.join(categories),
                            text]
                csv_writer.writerow(csv_line)
            db.close()
    f.close()


def main():
    # result_file = click.prompt('result file')
    result_file = './csv/sentences_train_result.csv'
    # sentence_word_file = click.prompt('sentence_word file')
    sentence_word_file = './csv/sentences_train.csv'
    post_category_dic = build_post_category_dic(iter_csv(sentence_word_file))
    lda_result_dic = build_lda_result_dic(iter_csv(result_file), post_category_dic)
    retrieve_full_sentence(lda_result_dic, './csv/sentences_train_text.csv')





if __name__ == '__main__':
    main()
