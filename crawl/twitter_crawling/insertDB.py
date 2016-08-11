# -*- coding: utf-8 -*-

import MySQLdb as mdb
import traceback
import os
from time import strftime
import imp
parsing = imp.load_source('parsing', '../../modules/parsing.py')
database_info = imp.load_source('database_info', '../../database_info.py')
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
flogname = './log/insert.log'

def get_time():
    return strftime('%Y-%m-%d %H:%M:%S')

def logging(text):
    with open(flogname, 'a') as log: log.write(('[%s] ' % get_time()) + text + '\n')

def reset_db(topic_name, source_name):
    logging('delete start')
    db = mdb.connect(**database_info.mysql_info())
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

    # del sources
    cur.execute('delete from sources where _id = %s', (source_id, ))

    db.commit()
    logging('delete complete')


def tuplize(s):
    return (s,)

def insert_query(title, timestamp, sentences, morphs_list):
    try:
        ### DB connected ###
        db = mdb.connect(**database_info.mysql_info())
        cur = db.cursor()

        # insert posts
        cur.execute('insert into posts (topic_id, source_id, title, timestamp)\
                    values (%s, %s, %s, %s)', (topic_id, source_id, title, timestamp))
        post_id = cur.lastrowid

        for i in range(len(sentences)):
            sentence = sentences[i]
            # insert sentence
            try:
                cur.execute('insert into sentences (post_id, sentence_seq, full_text)\
                            values (%s, %s, %s)', (post_id, i, sentence))
            except:
                logging('FAIL to insert sentence: %s' % sentence)
                pass

            morphs = morphs_list[i]

            # insert words which is newly appeared in the sentence
            dedups = parsing.dedup(morphs)
            cur.executemany('insert ignore into words (word) values (%s)', map(tuplize, dedups))

            for j in range(len(morphs)):
                # insert sentence word relation
                try:
                    cur.execute('insert into sentence_word_relations (post_id, sentence_seq, word_seq, word_id)\
                                select %s, %s, %s, _id from words where word=%s', (post_id, i, j, morphs[j]))
                except:
                    logging('FAIL to insert sentence_word_relations : %s, %s, %s, %s' % (post_id, i, j, morphs[j]))
                    pass

        db.commit()
        db.close()
        ### DB close ###
    except:
        logging('error while inserting %s'% title)
        logging(str(sys.exc_info()))
        return False
    return True

def store_posts(topic_name, source_name, source):
    ### DB connected ###
    db = mdb.connect(**database_info.mysql_info())
    cur = db.cursor()

    # get topic_id
    global topic_id
    topic_id = None
    cur.execute('select _id from topics where name=%s', (topic_name, ))
    results = cur.fetchall()
    if results:
        topic_id = results[0][0]
    else:
        logging('insert topic: %s' % topic_name)
        cur.execute('insert into topics (name) values (%s)', (topic_name, ))
        topic_id = cur.lastrowid

    # get source_id
    global source_id
    source_id = None
    cur.execute('select _id from sources where name=%s', (source_name, ))
    results = cur.fetchall()
    if results:
        source_id = results[0][0]
    else:
        logging('insert source: %s' % source_name)
        cur.execute('insert into sources (name) values (%s)', (source_name, ))
        source_id = cur.lastrowid

    # get existing posts list
    cur.execute('select title from posts where topic_id=%s and source_id=%s', (topic_id, source_id))
    posts = [row[0] for row in cur.fetchall()]
    db.commit()
    db.close()
    ### DB cloase ###

    # get file lists
    dirname = './posts/' + source
    files = os.listdir(dirname)
    files.sort()
    for filename in files:
        logging('inserting file: %s' % filename)

        # skip already-inserted files
        if '.'.join(filename.split('.')[0:-1]) in posts:
            logging('%s is already exists' % filename)
            continue

        f = open(os.path.join(dirname, filename))
        lines = parsing.convert_textfile_to_lines(f)

        title = lines[0].strip()
        lines = lines[1:]
        timestamp = ' '.join(filename.split(' - ')[1].split(' ')[0:2])

        sentences = parsing.do_sentencing_without_threading(lines)
        morphs_list = {}

        for i in range(len(sentences)):
            sentence = sentences[i]
            morphs = map(parsing.concate_tuple, parsing.do_parsing_without_threading(sentence))
            if morphs:
                morphs_list[i] = morphs
            else:
                morphs_list[i] = []

        if insert_query(title, timestamp, sentences, morphs_list):
            logging('........ done')
        else:
            logging('........ fail')

if __name__ == '__main__':
    store_posts(u'자살', 'twitter 08', 'posts_08')
