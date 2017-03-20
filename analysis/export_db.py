#-*- coding: utf-8 -*-
import click
import MySQLdb as mdb
import cPickle as pickle
from collections import defaultdict
import os
import csv
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import imp
database_info = imp.load_source('database_info', '../database_info.py')
mysql_info = database_info.mysql_info


class Utils(object):
    @staticmethod
    def strip_all(obj):
        for e in obj:
            try:
                yield e.strip()
            except:
                yield e


class Exporter(object):
    unnecessaries = ['Josa', 'Determiner', 'Conjunction', 'Exclamation', 'PreEomi',
                     'Eomi', 'Suffix', 'Punctuation', 'Foreign', 'Alpha', 'Number',
                     'Unknown', 'KoreanParticle', 'Hashtacg', 'ScreenName']
    WORD_START = 231243
    WORD_END = 352484
    WORD_LIMIT = WORD_END - WORD_START + 1

    def __init__(self, **kwargs):
        self.path = kwargs.get('path')
        self.update = kwargs.get('update', False)

    @staticmethod
    def save_file(obj, path, update=False):
        if not os.path.isfile(path) or update:
            _, ext = os.path.splitext(path)
            with open(path, 'w') as f:
                if ext == '.csv':
                    csv_file = csv.writer(f, delimiter=',')
                    with click.progressbar(obj, label='Writing CSV file.') as bar:
                        for line in bar:
                            striped = list(Utils.strip_all(line))
                            csv_file.writerow(striped)
                elif ext == '.pkl':
                    pickle.dump(obj, f)

    def export_texts(self, **kwargs):
        path = os.path.join(kwargs.get('path', self.path), 'texts.csv')
        update = kwargs.get('update', self.update)
        assert not os.path.isfile(path) or update, 'texts.csv is already exists'
        fname, ext = os.path.splitext(path)
        with mdb.connect(**mysql_info()) as db:
            query = """\
                    select s.post_id, s.sentence_seq, s.full_text
                    from sentences as s
                    join posts as p
                    on p._id = s.post_id
                    join sources as sr
                    on sr._id = p.source_id
                    where sr._id between 4 and 7
                    """
            db.execute(query)
            results = db.fetchall()
            self.save_file(results, fname+'.csv', update)

    def export_words(self, **kwargs):
        path = os.path.join(kwargs.get('path', self.path), 'words.csv')
        update = kwargs.get('update', self.update)
        assert not os.path.isfile(path) or update, 'words.csv is already exists'
        with mdb.connect(**mysql_info()) as db:
            dic = defaultdict(list)
            query = """\
                    select word, count(*) as count
                    from (select _id, word
                        from words
                        limit {limit} offset {offset}) as w
                    join sentence_word_relations as r
                    on w._id = r.word_id
                    group by word
                    """.format(limit=self.WORD_LIMIT, offset=self.WORD_START)
            db.execute(query)
            for line in db.fetchall():
                tag = line[0].split('_')[-1]
                dic[tag].append(line)
            print 'Data have fetched'
            fname, ext = os.path.splitext(path)
            self.save_file(dic, fname+'.pkl', update)
            words = (word for words in dic.values() for word in words)
            self.save_file(words, fname+'.csv', update)

    def export_sentences_labeled(self, **kwargs):
        path = os.path.join(kwargs.get('path', self.path), 'sentences_labeled.csv')
        update = kwargs.get('update', self.update)
        assert not os.path.isfile(path) or update, 'sentences_labeled.csv is already exists'
        with mdb.connect(**mysql_info()) as db:
            query = """\
                    select r.post_id, r.sentence_seq, r.categories, s.words
                    from (select r.post_id, r.sentence_seq,
                            group_concat(rs.category_seq separator ' ') as categories
                        from rule_sentence_relations as r
                        join rules as rs
                        on r.rule_id = rs._id
                        join posts as p
                        on r.post_id = p._id
                        where p.source_id between 4 and 7
                        group by r.post_id, r.sentence_seq) as r
                    join (select s.post_id, s.sentence_seq,
                            group_concat(w.word separator ' ') as words
                        from sentence_word_relations as s
                        join (select _id, word from words limit {limit} offset {offset}) AS w
                        on s.word_id = w._id
                        join posts as p
                        on p._id = s.post_id
                        where p.source_id between 4 and 7
                        group by s.post_id, s.sentence_seq) as s
                    on r.post_id = s.post_id and r.sentence_seq = s.sentence_seq
                    """.format(limit=self.WORD_LIMIT, offset=self.WORD_START)
            db.execute(query)
            self.save_file(db.fetchall(), path, update)

    def export_sentences_all(self, **kwargs):
        path = os.path.join(kwargs.get('path', self.path), 'sentences_all.csv')
        update = kwargs.get('update', self.update)
        assert not os.path.isfile(path) or update, 'sentences_all.csv is already exists'
        with mdb.connect(**mysql_info()) as db:
            query = """\
                    select s.post_id, s.sentence_seq,
                        group_concat(w.word separator ' ') as words
                    from sentence_word_relations as s
                    left join rule_sentence_relations as r
                    on s.post_id = r.post_id and s.sentence_seq = r.sentence_seq
                    join (select _id, word from words limit {limit} offset {offset}) AS w
                    on s.word_id = w._id
                    join posts as p
                    on p._id = s.post_id
                    where r.post_id is null
                    and p.source_id between 4 and 7
                    group by s.post_id, s.sentence_seq
                    """.format(limit=self.WORD_LIMIT, offset=self.WORD_START)
            db.execute(query)
            self.save_file(db.fetchall(), path, update)

    def export_rule_text(self, **kwargs):
        path = os.path.join(kwargs.get('path', self.path), 'sentences_labeled_by_user.csv')
        update = kwargs.get('update', self.update)
        assert not os.path.isfile(path) or update, 'sentences_labeled_by_user.csv is already exists'
        with mdb.connect(**mysql_info()) as db:
            query = """\
                select category_seq, full_text from rules
                """
            db.execute(query)
            self.save_file(db.fetchall(), path, update)

    def export_rulesets(self, **kwargs):
        path = os.path.join(kwargs.get('path', self.path), 'rulesets.csv')
        update = kwargs.get('update', self.update)
        assert not os.path.isfile(path) or update, 'sentences_labeled_by_user.csv is already exists'
        with mdb.connect(**mysql_info()) as db:
            query = """\
                select category_seq, name from rulesets
            """
            db.execute(query)
            self.save_file(db.fetchall(), path, update)


def main():
    # export_words('words', True)
    # export_sentences_trainset('sentences_train.csv')
    exporter = Exporter(path='./csv170219')
    # exporter.export_words()
    # exporter.export_sentences_labeled()
    exporter.export_sentences_all()


if __name__ == '__main__':
    main()
