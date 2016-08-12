# -*- coding: utf-8 -*-

from konlpy.utils import pprint
import MySQLdb as mdb
import redis
from celery import Celery
import _mysql_exceptions
import ast
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify
import logging
from logging.handlers import RotatingFileHandler
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from modules.parsing import convert_textfile_to_lines, do_sentencing_without_threading, do_parsing_without_threading, dedup, concate_tuple, do_parsing_by_threading
from modules.crawling import crawl
from analysis import analyze
from database_info import mysql_info, redis_info

import jpype
from time import time

app = Flask(__name__)
# app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
# app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)



# Should be modified later. this is just from tutorial.
app.config.update(dict(
    DATABASE = '/tmp/morpheme.db',
    DEBUG = True,
    SECRET_KEY = 'development key',
    USERNAME = 'admin',
    PASSWORD = 'default'
    ))
app.config.from_envvar('FLASK_SETTINGS', silent=True)

config = dict(
    perpage   =   10
)

queries = {
    # param: topic_name
    'add_topic'                 :   'INSERT INTO topics (name) VALUES (%s)',
    # param:
    'get_topics'                :   'SELECT _id, name FROM topics',

    # param: source_name
    'add_source'                :   'INSERT INTO sources (name) VALUES (%s)',
    # param:
    'get_sources'               :   'SELECT _id, name FROM sources',

    # param: topic_id, source_id, title, url
    'add_post'                  :   'INSERT INTO posts (topic_id, source_id, title, url, timestamp) VALUES (%s, %s, %s, %s, %s)',

    'get_posts_count'           :   'SELECT COUNT(*) FROM posts WHERE topic_id = {} AND source_id in ({})',

    # param: topic_id, source_ids_string
    'get_posts'                 :   'SELECT _id, title, url, DATE_FORMAT(timestamp, "%Y/%m/%d") FROM posts WHERE topic_id = {} AND source_id IN ({})',

    # param: post_id, sentence_seq, full_text
    'add_sentence'              :   'INSERT INTO sentences (post_id, sentence_seq, full_text) VALUES (%s, %s, %s)',
    # param: post_id
    'get_sentences'             :   'SELECT sentence_seq, full_text FROM sentences\
                                     WHERE post_id = %s ORDER BY sentence_seq ASC',
    'get_sentences_'            :   'SELECT r.rnum, s.full_text \
                                     FROM sentences AS s \
                                     JOIN (%s) AS r ON s.post_id = r.post_id AND s.sentence_seq = r.sentence_seq \
                                     WHERE r.post_id = %s \
                                     ORDER BY rnum ASC',
    # param: sentence_ids
    'get_sentences_by_rule_'    :   'SELECT r.rnum AS sentence_id, s.full_text \
                                     FROM sentences AS s \
                                     JOIN (%s) AS r ON s.post_id = r.post_id AND s.sentence_seq = r.sentence_seq \
                                     WHERE r.rnum IN (%s) \
                                     ORDER BY rnum ASC',

    'get_sentences_by_rule'     :   'SELECT  (@rnum:=@rnum+1) AS rnum, s.full_text\
                                     FROM    sentences AS s\
                                     JOIN    (SELECT post_id, sentence_seq\
                                              FROM   rule_sentence_relations\
                                              WHERE  rule_id = %s) AS t\
                                     ON      s.post_id = t.post_id\
                                     AND     s.sentence_seq = t.sentence_seq\
                                     JOIN    (SELECT @rnum:=-1) AS r',

    'get_sentences_by_ruleset'  :   'SELECT  (@rnum:=@rnum+1) AS rnum, s.full_text, t.rule_ids\
                                     FROM    sentences AS s\
                                     JOIN    (SELECT rel.post_id, rel.sentence_seq, GROUP_CONCAT(rel.rule_id SEPARATOR ",") AS rule_ids\
                                             FROM   rule_sentence_relations AS rel\
                                             JOIN   rules\
                                             ON     rules._id = rel.rule_id\
                                             WHERE  rules.category_seq = %s\
                                             GROUP BY rel.post_id, rel.sentence_seq) AS t\
                                     ON      s.post_id = t.post_id\
                                     AND     s.sentence_seq = t.sentence_seq\
                                     JOIN    (SELECT @rnum:=-1) AS r',

    # param: topic, sentence_seqs
    'get_post_sentences_rel'    :   'SELECT post_id, sentence_seq FROM (%s) AS t WHERE rnum IN (%s)',
    'get_rnums_of_sentences'    :   'SELECT n.rnum, n.post_id, n.sentence_seq FROM (%s) AS n JOIN (%s) AS p on n.post_id = p._id',

    # param: word
    'add_word'                  :   'INSERT IGNORE INTO words (word) VALUES (%s)',

    # param: post_id, sentence_seq, word_weq, word
    'add_sentence_word_relation':   'INSERT INTO sentence_word_relations (post_id, sentence_seq, word_seq, word_id) \
                                     SELECT %s, %s, %s, _id FROM words WHERE word = %s',

    # param: topic_id, name, topic_id
    'add_ruleset'               :   'INSERT INTO rulesets (topic_id, category_seq, name) \
                                     SELECT %s, IFNULL(MAX(category_seq), 0) + 1, %s FROM rulesets WHERE topic_id = %s',
    # param: topic_id
    'get_ruleset'               :   'SELECT category_seq, name FROM rulesets WHERE topic_id = %s ORDER BY category_seq DESC LIMIT 1',
    # param: topic_id
    'get_rulesets'             :   'SELECT category_seq, name FROM rulesets WHERE topic_id = %s',
    'get_rulesets_'              :   'SELECT s.category_seq, s.name, r._id, r.full_text \
                                     FROM rulesets AS s \
                                     JOIN rules AS r \
                                     ON s.topic_id = r.topic_id AND s.category_seq = r.category_seq \
                                     WHERE topic_id = %s',
    # param: topic_id, category_seq
    'del_ruleset'               :   'DELETE FROM rulesets WHERE topic_id = %s and category_seq = %s',
    # param: topic_id, category_seq
    'del_rules'                 :   'DELETE FROM rules WHERE topic_id = %s and category_seq = %s',
    # param: topic_id, category_seq
    'del_rules_word_relations'  :   'DELETE FROM rule_word_relations WHERE rule_id IN \
                                     (SELECT _id FROM rules WHERE topic_id = %s and category_seq = %s)',
    'del_rules_sentence_relations': 'DELETE FROM rule_sentence_relations WHERE rule_id IN \
                                     (SELECT _id FROM rules WHERE topic_id = %s and category_seq = %s)',

    # param: topic_id, category_seq, full_text
    'add_rule'                  :   'INSERT INTO rules (topic_id, category_seq, full_text) VALUES (%s, %s, %s)',
    # param: topic_id, category_seq
    'get_rules'                 :   'SELECT rule_id, word FROM rules AS A \
                                     INNER JOIN rule_word_relations AS B ON A._id = B.rule_id \
                                     INNER JOIN words AS C ON B.word_id = C._id \
                                     WHERE A.topic_id = %s AND A.category_seq = %s',
    'get_all_rules'             :   'SELECT _id FROM rules WHERE topic_id = %s',
    'get_rules_'                :   'SELECT A.category_seq, rule_id, full_text, word \
                                     FROM rules AS A \
                                     INNER JOIN rule_word_relations AS B ON A._id = B.rule_id \
                                     INNER JOIN words AS C ON B.word_id = C._id \
                                     WHERE A.topic_id = %s AND A.category_seq in (%s)',

    # param: rule_id
    'del_rule'                  :   'DELETE FROM rules WHERE _id = %s',
    # param: rule_id
    'del_rule_word_relations'   :   'DELETE FROM rule_word_relations WHERE rule_id = %s',
    'del_rule_sentence_relations':  'DELETE FROM rule_sentence_relations WHERE rule_id = %s',

    # param: rule_id, word_seq, word
    'add_rule_word_relation'    :   'INSERT INTO rule_word_relations (rule_id, word_seq, word_id) \
                                     SELECT %s, %s, _id FROM words WHERE word = %s',
    # param:
    'get_word_sentences'        :   'SELECT word_id, GROUP_CONCAT(rnum SEPARATOR ",") AS sentences \
                                     FROM (SELECT DISTINCT s.rnum, r.word_id \
                                           FROM (SELECT @rnum:=@rnum+1 AS rnum, t.post_id, t.sentence_seq \
                                                 FROM (SELECT * FROM sentences order by post_id, sentence_seq) AS t, (SELECT @rnum:=-1) AS r) AS s \
                                           JOIN sentence_word_relations AS r ON s.post_id = r.post_id and s.sentence_seq = r.sentence_seq \
                                           JOIN words AS w ON r.word_id = w._id) AS t \
                                     GROUP BY word_id', # for redis
    # param: topic_id
    'get_rule_words'            :   'SELECT category_seq, rule_id, (MAX(word_seq) - MIN(word_seq)) AS gap, GROUP_CONCAT(word_id ORDER BY word_seq SEPARATOR ",") AS words \
                                     FROM (SELECT r.category_seq, rw.rule_id, rw.word_seq, rw.word_id \
                                           FROM rule_word_relations AS rw \
                                           JOIN rules AS r ON r._id = rw.rule_id \
                                           WHERE r.topic_id = %s \
                                           ORDER BY word_seq) AS t \
                                     GROUP BY rule_id',
    # param: word_id
    'get_sentence_words_'       :   'SELECT rnum, GROUP_CONCAT(word_seq SEPARATOR ",") AS word_seqs, GROUP_CONCAT(word_id SEPARATOR ",") AS word_ids \
                                     FROM (SELECT t.rnum, r.word_seq, r.word_id \
                                           FROM (SELECT (@rnum:=@rnum+1) AS rnum, post_id, sentence_seq \
                                                 FROM (SELECT * FROM sentences ORDER BY post_id, sentence_seq) AS s, (SELECT @rnum:=0) AS r) AS t \
                                           JOIN sentence_word_relations AS r ON t.post_id = r.post_id and t.sentence_seq = r.sentence_seq \
                                           WHERE word_id IN (%s) \
                                           ORDER BY word_seq) AS t \
                                     GROUP BY rnum', # not used
    # param: topic_id, source_ids_string, word_ids_string, word_ids_string, len(word_ids_string)
    'get_sentence_words'        :   'SELECT t1.post_id, t1.sentence_seq, GROUP_CONCAT(word_seq ORDER BY word_seq SEPARATOR ",") AS word_seqs, \
                                            GROUP_CONCAT(word_id ORDER BY word_seq SEPARATOR ",") AS word_ids \
                                     FROM (SELECT s.post_id, s.sentence_seq, r.word_seq, r.word_id FROM sentences AS s \
                                           JOIN sentence_word_relations AS r ON s.post_id = r.post_id AND s.sentence_seq = r.sentence_seq \
                                           JOIN posts AS p ON p._id = s.post_id \
                                           WHERE p.topic_id = %s AND p.source_id IN (%s) AND r.word_id IN (%s) ORDER BY word_seq) AS t1 \
                                     JOIN (SELECT s.post_id, s.sentence_seq, COUNT(*) AS cat_count \
                                           FROM sentences AS s \
                                           JOIN sentence_word_relations AS r ON s.post_id = r.post_id AND s.sentence_seq = r.sentence_seq \
                                           WHERE r.word_id IN (%s) \
                                           GROUP BY s.post_id, s.sentence_seq having cat_count >= %s) AS t2 \
                                     ON t1.post_id = t2.post_id AND t1.sentence_seq = t2.sentence_seq \
                                     GROUP BY post_id, sentence_seq', # topic, sources, words, words, numberOfWords
    # param: topic_id, source_ids_string
    'get_sentences_rnum'        :   'SELECT @rnum:=@rnum+1 AS rnum, t.post_id, t.sentence_seq \
                                     FROM (SELECT s.post_id, s.sentence_seq \
                                           FROM sentences AS s \
                                           JOIN posts AS p ON s.post_id = p._id \
                                           WHERE p.topic_id = %s AND p.source_id IN (%s)) AS t, \
                                     (SELECT @rnum:=0) AS r',
    # param: queries[get_sentence_words], queries[get_sentences_rnum]
    'get_sentence_words_rnum'   :   'SELECT r.post_id, r.rnum as sentence_id, t.word_seqs, t.word_ids \
                                     FROM (%s) AS t \
                                     JOIN (%s) AS r \
                                     ON t.post_id = r.post_id AND t.sentence_seq = r.sentence_seq',

    # param: topic_id, sources_ids, topic_id
    'get_result_by_rule'        :   'SELECT t.rule_id,\
                                             COUNT(*) AS c\
                                     FROM   (SELECT r.rule_id, r.post_id, r.sentence_seq\
                                             FROM   rule_sentence_relations AS r\
                                                     join (SELECT _id AS post_id\
                                                         FROM   posts\
                                                         WHERE  topic_id = %s\
                                                                 AND source_id IN (%s)) AS p\
                                                     ON r.post_id = p.post_id\
                                                     join (SELECT _id AS rule_id\
                                                         FROM   rules\
                                                         WHERE  topic_id = %s) AS rules\
                                                     ON r.rule_id = rules.rule_id) AS t\
                                     GROUP  BY t.rule_id',

    # param: topic_id, source_ids, rnum start, rnum endt
    'get_result_by_post'        :   'SELECT a.post_id, b.category_seq, COUNT(*) AS count\
                                     FROM   rule_sentence_relations AS a\
                                     JOIN   rules AS b\
                                     ON     a.rule_id = b._id\
                                     JOIN   (SELECT _id, topic_id\
                                             FROM   posts\
                                             WHERE  topic_id = %s\
                                             AND    source_id IN (%s)\
                                             LIMIT  %s, %s) AS c\
                                     ON     c.topic_id = b.topic_id\
                                     AND    c._id = a.post_id\
                                     GROUP  BY a.post_id, b.category_seq',

    # param: post_id, sentence_seq
    'get_result_by_sentence'    :   'SELECT rule_id FROM rule_sentence_relations\
                                     WHERE post_id = %s and sentence_seq = %s'
    }


# Should be modified when it be deployed.
def connect_db():
    conn = mdb.connect(**mysql_info())
    return conn

def connect_redis():
    rd = redis.StrictRedis(**redis_info())
    return rd

# Only execute at the first time.
def init_db():
    rd = connect_redis()
    rd.flushall()
    db = connect_db()
    with db:
        with app.open_resource('schema.sql') as f:
            cursor = db.cursor()
            query = ''
            while(True):
                query_line = f.readline()
                if not query_line: break
                query += query_line
                if ';' in query:
                    print query
                    cursor.execute(query)
                    print 'Success'
                    query = ''
    db.close()

# not used
def build_bitarray(length, index_array):
    bitarray = [False]*length
    for i in index_array:
        bitarray[i] = True
    return bitarray

# not used
def build_redis():
    rd =connect_redis()
    rd.flushall()
    db = connect_db()
    cur = db.cursor()
    cur.execute(queries['get_word_sentences'])
    pipe = rd.pipeline()
    for row in cur.fetchall():
        for i in map(int, row[1].split(',')):
            pipe.setbit('word_'+str(row[0]), i, 1)
    pipe.execute()

def tuplize(s):
    return (s,)

def formatstring(arr):
    if type(arr) == list:
        return ', '.join(['%s']*len(arr))
    else:
        return '%s'
def formatstringBracket(arr):
    if type(arr) == list:
        return ', '.join(['{}']*len(arr))
    else:
        return '{}'


def store_posts(topic_name, source_name):
    db = connect_db()
    cur = db.cursor()

    cur.execute(queries['add_topic'], (topic_name, ))
    topic_id = cur.lastrowid
    cur.execute(queries['add_source'], (source_name, ))
    source_id = cur.lastrowid

    files = crawl()
    print files;
    for fname in files:
        f = open(fname)
        print 'inserting %s' %fname

        lines = convert_textfile_to_lines(f)

        title = lines[0]
        url = lines[1]
        lines = lines[2:]
        timestamp = fname.split('/')[-1].split('_')[0]

        # insert post
        cur.execute(queries['add_post'], (topic_id, source_id, title, url, timestamp))
        post_id = cur.lastrowid

        sentences = do_sentencing_without_threading(lines)
        for i in range (len(sentences)):
            # insert sentence
            sentence = sentences[i]
            cur.execute(queries['add_sentence'], (post_id, i, sentence))

            # insert newly appeared words.
            morphs = map(concate_tuple, do_parsing_without_threading(sentence))
            cur.executemany(queries['add_word'], map(tuplize, dedup(morphs)))

            # insert relations
            for j in range(len(morphs)):
                cur.execute(queries['add_sentence_word_relation'], (post_id, i, j, morphs[j]))

        db.commit()
        print 'Done'
    db.close()

@app.before_request
def before_request():
    g.db = connect_db()
    g.rd = connect_redis()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

@app.route('/')
def initialize_page():
    app.logger.info('Initial Page')

    cur = g.db.cursor()
    cur.execute(queries['get_topics'])
    topics = [dict(id=int(row[0]), name=row[1]) for row in cur.fetchall()]
    cur.execute(queries['get_sources'])
    sources = [dict(id=int(row[0]), name=row[1]) for row in cur.fetchall()]
    return render_template('show_posts.html', topics=topics, sources=sources)


def get_post_between(cur, topic, sources_ids, start, number):
    cur.execute(queries['get_posts'].format('{}', formatstringBracket(sources_ids))\
                                    .format(topic, *sources_ids) + 'LIMIT %s, %s'%(start, number))
    return cur


def get_post_ruleset_count_dic(cur, topic, sources_ids, start, end):
    format_string = formatstring(sources_ids)
    post_ruleset_count_dic = {}
    cur.execute(queries['get_result_by_post']%('%s', format_string, '%s', '%s'),\
                [topic] + sources_ids + [start, end])

    for row in cur.fetchall():
        post_id, category_seq, count = map(int, row)
        if post_id in post_ruleset_count_dic:
            post_ruleset_count_dic[post_id][category_seq] = count
        else:
            post_ruleset_count_dic[post_id] = {category_seq: count}

    return post_ruleset_count_dic


def get_rule_count_dic(cur, topic, sources_ids):
    format_string = formatstring(sources_ids)
    cur.execute(queries['get_all_rules'], (topic, ))
    # rule_count_dic = {row[0]: 0 for row in cur.fetchall()}
    rd = g.rd
    rule_count_dic = {k: 0 for k in map(long, rd.keys())}

    cur.execute(queries['get_result_by_rule']%('%s', format_string, '%s'), [topic]+sources_ids+[topic] )
    for row in cur.fetchall():
        rule_count_dic[row[0]] = row[1]
    return rule_count_dic


@app.route('/_posts', methods=['GET'])
def posts():
    if request.method == 'GET':
        topic = ast.literal_eval(request.args.get('topic'))
        sources_ids = ast.literal_eval(request.args.get('sources'))
        format_string = formatstring(sources_ids)
        format_string_bracket = formatstringBracket(sources_ids)

        app.logger.info('GET posts: topic(%s), sources_ids(%s)'%('%s', format_string)%tuple([topic]+sources_ids))

        db = g.db
        cur = db.cursor()

        cur.execute(queries['get_posts_count'].format('{}', format_string_bracket).format(topic, *sources_ids))
        posts_count = cur.fetchall()[0][0]

        get_post_between(cur, topic, sources_ids, 0, config['perpage'])
        posts = [dict(id=int(row[0]), title=row[1], url=row[2], timestamp=row[3]) for row in cur.fetchall()]

        cur.execute(queries['get_rulesets'], (topic, ))
        rulesets = [dict(category_seq=int(row[0]), name=row[1]) for row in cur.fetchall()]

        ruleset_rules_dic = {}
        rule_ruleset_dic = {}
        for ruleset in rulesets:
            category_seq = ruleset['category_seq']
            cur.execute(queries['get_rules'], (topic, category_seq))
            rule_dic = {}
            for row in cur.fetchall():
                rule_id = int(row[0])
                word = row[1]
                word = word[:word.rindex('_')]
                if rule_id not in rule_ruleset_dic:
                    rule_ruleset_dic[rule_id] = category_seq
                if rule_id not in rule_dic:
                    rule_dic[rule_id] = [word]
                else:
                    rule_dic[rule_id].append(word)
            rules = [dict(rule_id=int(key), word=val) for key, val in rule_dic.iteritems()]
            ruleset_rules_dic[category_seq] = rules

        rule_count_dic = get_rule_count_dic(cur, topic, sources_ids)

        post_ruleset_count_dic = get_post_ruleset_count_dic(cur, topic, sources_ids, 0, config['perpage'])

        return jsonify(posts_count              = posts_count, \
                       posts                    = posts, \
                       rulesets                 = rulesets, \
                       ruleset_rules_dic        = ruleset_rules_dic, \
                       rule_count_dic           = rule_count_dic, \
                       post_ruleset_count_dic   = post_ruleset_count_dic)


@app.route('/_posts_by_page', methods=['GET'])
def posts_by_page():
    if request.method == 'GET':
        topic = ast.literal_eval(request.args.get('topic'))
        sources_ids = ast.literal_eval(request.args.get('sources'))
        format_string = formatstring(sources_ids)
        format_string_bracket = formatstringBracket(sources_ids)
        page = ast.literal_eval(request.args.get('page'))

        # app.logger.info('GET posts_by_page: topic(%s), sources_ids(%s), page(%s)'%('%s', format_string, '%s')%tuple([topic]+[sources_ids]+[page]))

        db = g.db
        cur = db.cursor()

        from_post_rnum = (page-1)*config['perpage']
        get_post_between(cur, topic, sources_ids, from_post_rnum, config['perpage'])
        posts = [dict(id=int(row[0]), title=row[1], url=row[2], timestamp=row[3]) for row in cur.fetchall()]

        post_ruleset_count_dic = get_post_ruleset_count_dic(cur, topic, sources_ids, from_post_rnum, config['perpage'])

        return jsonify(posts                    = posts,\
                       post_ruleset_count_dic   = post_ruleset_count_dic)

@app.route('/_sentences', methods=['GET'])
def sentences():
    if request.method == 'GET':
        topic = ast.literal_eval(request.args.get('topic'))
        sources_ids = ast.literal_eval(request.args.get('sources'))
        format_string = formatstring(sources_ids)
        post_id = ast.literal_eval(request.args.get('post_id'))

        app.logger.info('GET sentneces: topic(%s), sources_ids(%s), post_id(%s)'%('%s',format_string, '%s')%tuple([topic]+sources_ids+[post_id]))

        cur = g.db.cursor()
        cur.execute(queries['get_sentences'], (post_id, ))

        sentences = []
        for row in cur.fetchall():
            sentence_id = int(row[0])
            full_text = row[1]
            cur.execute(queries['get_result_by_sentence'], (post_id, sentence_id))
            rules = [row[0] for row in cur.fetchall()]
            sentences.append(dict(sentence_id=sentence_id, full_text=full_text, rules=rules))
        return jsonify(sentences=sentences)

@app.route('/_sentences_by_rule', methods=['GET'])
def sentences_by_rule():
    if request.method == 'GET':
        topic = ast.literal_eval(request.args.get('topic'))
        sources_ids = ast.literal_eval(request.args.get('sources'))
        format_string = formatstring(sources_ids)
        isRuleset = True if request.args.get('isRuleset') == 'true' else False
        rule_id = ast.literal_eval(request.args.get('rule_id'))

        app.logger.info('GET sentences_by_rule: topic(%s), sources_ids(%s), isRuleset(%s), ruleset_or_rule_id(%s)'\
                %('%s',format_string, '%s', '%s')%tuple([topic]+sources_ids+[isRuleset, rule_id]))

        db = g.db
        cur = db.cursor()

        sentences = []
        if isRuleset:
            cur.execute(queries['get_sentences_by_ruleset'], (rule_id, ))
            sentences.extend([dict(sentence_id  = row[0],\
                                   full_text    = row[1],\
                                   rules        = map(int, row[2].split(',')))\
                              for row in cur.fetchall()])
        else:
            cur.execute(queries['get_sentences_by_rule'], (rule_id, ))
            sentences.extend([dict(sentence_id  = row[0],\
                                   full_text    = row[1],\
                                   rules        = [])\
                              for row in cur.fetchall()])

        return jsonify(sentences=sentences)

@app.route('/_rulesets', methods=['POST', 'DELETE'])
def rulesets():
    if request.method == 'POST':
        topic = ast.literal_eval(request.form['topic'])
        name = request.form['name']

        app.logger.info('POST rulesets: topic(%s), name(%s)'%(topic, name))

        db = g.db
        cur = db.cursor()
        cur.execute(queries['add_ruleset'], (topic, name, topic))
        db.commit()
        cur.execute(queries['get_ruleset'], (topic, ))
        rulesets = [dict(category_seq=int(row[0]), name=row[1]) for row in cur.fetchall()]
        return jsonify(rulesets=rulesets)

    if request.method == 'DELETE':
        topic = ast.literal_eval(request.form['topic'])
        category_seq = ast.literal_eval(request.form['category_seq'])

        app.logger.info('DELETE rulesets: topic(%s), category_seq(%s)'%(topic, category_seq))

        db = g.db
        cur = db.cursor()
        cur.execute(queries['get_rules'], (topic, category_seq))
        rd = g.rd
        for row in cur.fetchall():
            rd.delete(int(row[0]))
        cur.execute(queries['del_rules_word_relations'], (topic, category_seq))
        cur.execute(queries['del_rules_sentence_relations'], (topic, category_seq))
        cur.execute(queries['del_rules'], (topic, category_seq))
        cur.execute(queries['del_ruleset'], (topic, category_seq))
        db.commit()
        return jsonify(deleted=dict(topic=topic, category_seq=category_seq))


@app.route('/_parsing', methods=['GET'])
def parsing():
    text = request.args.get('text')

    app.logger.info('GET parsing: text(%s)'%(text))

    jpype.attachThreadToJVM()
    return jsonify(morphs=do_parsing_without_threading(text))

@app.route('/_rules', methods=['POST', 'DELETE'])
def rules():
    if request.method == 'POST':
        topic = ast.literal_eval(request.form['topic'])
        category_seq = ast.literal_eval(request.form['category_seq'])
        ruleText = request.form['ruleText']
        checked = ast.literal_eval(request.form['checked'])

        app.logger.info('POST rules: text(%s), words(%s)'%('%s', formatstring(checked))%tuple([ruleText]+checked))

        db = g.db
        cur = db.cursor()
        cur.executemany(queries['add_word'], map(tuplize, [x['word'] for x in checked]))
        cur.execute(queries['add_rule'], (topic, category_seq, ruleText))
        rule_id = cur.lastrowid
        words = []
        for x in checked:
            word = x['word']
            words.append(word)
            seq = x['seq']
            cur.execute(queries['add_rule_word_relation'], (rule_id, seq, word))
        db.commit()
        words = map(lambda x: x[:x.rindex('_')], words)
        rules = [dict(rule_id=int(rule_id), full_text=ruleText, word=words)]
        return jsonify(rules=rules)
    elif request.method == 'DELETE':
        rule_id = ast.literal_eval(request.form['rule_id'])

        app.logger.info('DELETE rules: rule_id(%s)'%(rule_id))

        rd = g.rd
        if rd.exists(rule_id):
            rd.delete(rule_id)
        db = g.db
        cur = db.cursor()
        cur.execute(queries['del_rule_word_relations'], (rule_id, ))
        cur.execute(queries['del_rule_sentence_relations'], (rule_id, ))
        cur.execute(queries['del_rule'], (rule_id, ))
        db.commit()
        return jsonify(deleted=dict(rule_id=rule_id))

def retrieve_sentence_ids(rd, keys):
    ret = []
    for key in keys:
        rd.set('tmp', rd.get(key))
        while(True):
            pos = rd.bitpos('tmp', 1)
            if pos < 0: break
            ret.append(int(pos))
            rd.setbit('tmp', pos, 0)
        rd.delete('tmp')
    return ret

def is_valid_sentences(gap, rule_word_ids, word_seqs, sentence_word_ids):
    previous_word_id = rule_word_ids[0]
    previous_position = -1
    i, j = 0, 0
    while(i < len(rule_word_ids) and j < len(sentence_word_ids)):
        rule_word_id = rule_word_ids[i]
        sentence_word_id = sentence_word_ids[j]
        if sentence_word_id == rule_word_id:
            if i == 0  or word_seqs[j] - previous_position <= gap:
                previous_word_id = rule_word_id
                previous_position = word_seqs[j]
                i += 1
                j += 1
                continue
        if sentence_word_id == previous_word_id:
            previous_position = word_seqs[j]
            j += 1
            continue
        j += 1
    if i == len(rule_word_ids):
        return True
    else:
        return False

@app.errorhandler(Exception)
def internal_error(exception):
    app.logger.error(exception)

@app.route('/_analysis', methods=['POST'])
def analysis():
    if request.method == 'POST':
        topic = ast.literal_eval(request.form['topic'])
        sources_ids = ast.literal_eval(request.form['sources'])
        source_format_string = formatstring(sources_ids)
        page = ast.literal_eval(request.form['page'])

        app.logger.info('POST anaysis: topic(%s), sources_ids(%s)'%('%s', source_format_string)%tuple([topic]+sources_ids))

        analyze(topic, sources_ids)

        db = g.db
        cur = db.cursor()
        rule_count_dic = get_rule_count_dic(cur, topic, sources_ids)

        from_post_rnum = (page-1)*config['perpage']
        post_ruleset_count_dic = get_post_ruleset_count_dic(cur, topic, sources_ids, from_post_rnum, config['perpage'])

    return jsonify(rule_count_dic           = rule_count_dic,\
                   post_ruleset_count_dic   = post_ruleset_count_dic)

if __name__ == '__main__':
    # init_db()
    # store_posts('자살', '조선일보')
    # build_redis()
    formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler = RotatingFileHandler('./logs/usage.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    # app.run(debug=True)
    app.run()
