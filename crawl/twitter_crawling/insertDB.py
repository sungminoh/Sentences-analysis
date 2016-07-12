# -*- coding: utf-8 -*-

import MySQLdb as mdb
import os
import imp
parsing = imp.load_source('parsing', '../../modules/parsing.py')
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def reset_db(topic_name, source_name):
    print 'delete start'
    db = mdb.connect(host='localhost', user='root', passwd='', db='morpheme', charset='utf8')
    cur = db.cursor()

    cur.execute('select _id from topics where name=%s', (topic_name, ))
    topic_id = cur.fetchall()[0][0]

    source_id = None
    cur.execute('select _id from sources where name=%s', (source_name, ))
    results = cur.fetchall()
    if results:
        source_id = results[0][0]

    # del sentence word relations
    cur.execute('delete from sentence_word_relations\
        where post_id in\
        (select _id from posts where topic_id = %s and source_id = %s)', (topic_id, source_id))

    # del sentences
    cur.execute('delete from sentences\
        where post_id in\
        (select _id from posts where topic_id = %s and source_id = %s)', (topic_id, source_id))

    # del posts
    cur.execute('delete from posts where topic_id = %s and source_id = %s', (topic_id, source_id))

    print 'delete complete'


def tuplize(s):
    return (s,)


def store_posts(topic_name, source_name):
    db = mdb.connect(host='localhost', user='root', passwd='', db='morpheme', charset='utf8')
    cur = db.cursor()

    cur.execute('select _id from topics where name=%s', (topic_name, ))
    topic_id = cur.fetchall()[0][0]

    source_id = None
    cur.execute('select _id from sources where name=%s', (source_name, ))
    results = cur.fetchall()
    if results:
        source_id = results[0][0]
    else:
        print 'insert source: %s' % source_name
        cur.execute('insert into sources (name) values (%s)', (source_name, ))
        source_id = cur.lastrowid

    cur.execute('select title from posts where topic_id=%s and source_id=%s', (topic_id, source_id))
    posts = [row[0] for row in cur.fetchall()]

    dirname = './reversed'
    for filename in os.listdir(dirname):
        print 'inserting file: %s' % filename
        if filename in posts:
            print '%s is already exists' % filename
            continue

        f = open(os.path.join(dirname, filename))
        lines = parsing.convert_textfile_to_lines(f)

        title = lines[0].strip()
        lines = lines[1:]
        timestamp = ' '.join(filename.split(' - ')[1].split(' ')[0:2])

        cur.execute('insert into posts (topic_id, source_id, title, timestamp)\
                    values (%s, %s, %s, %s)', (topic_id, source_id, title, timestamp))
        post_id = cur.lastrowid

        sentences = parsing.do_sentencing_without_threading(lines)

        for i in range(len(sentences)):
            sentence = sentences[i]
            try:
                cur.execute('insert into sentences (post_id, sentence_seq, full_text)\
                            values (%s, %s, %s)', (post_id, i, sentence))
            except:
                pass

            morphs = map(parsing.concate_tuple, parsing.do_parsing_without_threading(sentence))
            dedups = parsing.dedup(morphs)
            cur.executemany('insert ignore into words (word) values (%s)', map(tuplize, dedups))

            for j in range(len(morphs)):
                try:
                    cur.execute('insert into sentence_word_relations (post_id, sentence_seq, word_seq, word_id)\
                                select %s, %s, %s, _id from words where word=%s', (post_id, i, j, morphs[j]))
                except:
                    pass

        db.commit()
        print 'done'
    db.close()

if __name__ == '__main__':
    store_posts(u'자살', 'twitter')
