# -*- coding: utf-8 -*-
import MySQLdb as mdb
import redis
import _mysql_exceptions
import ast
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from modules.parsing import convert_textfile_to_lines, do_sentencing_without_threading, do_parsing_without_threading, dedup, concate_tuple, do_parsing_by_threading
from modules.crawling import crawl

import jpype

app = Flask(__name__)


# Should be modified later. this is just from tutorial.
app.config.update(dict(
    DATABASE = '/tmp/morpheme.db',
    DEBUG = True,
    SECRET_KEY = 'development key',
    USERNAME = 'admin',
    PASSWORD = 'default'
    ))
app.config.from_envvar('FLASK_SETTINGS', silent=True)

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
    'add_post'                  :   'INSERT INTO posts (topic_id, source_id, title, url) VALUES (%s, %s, %s, %s)',
    # param: topic_id, source_ids_string
    'get_posts_'                :   'SELECT B._id, A.full_text FROM sentences AS A INNER JOIN posts AS B ON A.post_id = B._id \
                                     WHERE B.topic_id = %s and B.source_id IN (%s)', # not used
    # param: topic_id, source_ids_string
    'get_posts'                 :   'SELECT _id, title, url FROM posts WHERE topic_id = %s and source_id IN (%s)',

    # param: post_id, sentence_seq, full_text
    'add_sentence'              :   'INSERT INTO sentences (post_id, sentence_seq, full_text) VALUES (%s, %s, %s)',
    # param: post_id
    'get_sentences_'             :   'SELECT sentence_seq, full_text FROM sentences WHERE post_id = %s',
    'get_sentences'            :   'SELECT r.rnum, s.full_text \
                                     FROM sentences AS s \
                                     JOIN (%s) AS r ON s.post_id = r.post_id AND s.sentence_seq = r.sentence_seq \
                                     WHERE r.post_id = %s \
                                     ORDER BY rnum ASC',

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
                                     (SELECT _id FROM rules WHERE  topic_id = %s and category_seq = %s)',

    # param: topic_id, category_seq, full_text
    'add_rule'                  :   'INSERT INTO rules (topic_id, category_seq, full_text) VALUES (%s, %s, %s)',
    # param: topic_id, category_seq
    'get_rules'                 :   'SELECT rule_id, full_text, word FROM rules AS A \
                                     INNER JOIN rule_word_relations AS B ON A._id = B.rule_id \
                                     INNER JOIN words AS C ON B.word_id = C._id \
                                     WHERE A.topic_id = %s AND A.category_seq = %s',
    'get_rules_'                 :   'SELECT A.category_seq, rule_id, full_text, word \
                                     FROM rules AS A \
                                     INNER JOIN rule_word_relations AS B ON A._id = B.rule_id \
                                     INNER JOIN words AS C ON B.word_id = C._id \
                                     WHERE A.topic_id = %s AND A.category_seq in (%s)',

    # param: rule_id
    'del_rule'                  :   'DELETE FROM rules WHERE _id = %s',
    # param: rule_id
    'del_rule_word_relations'   :   'DELETE FROM rule_word_relations WHERE rule_id = %s',
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
    'get_rule_words'            :   'SELECT rule_id, (MAX(word_seq) - MIN(word_seq)) AS gap, GROUP_CONCAT(word_id SEPARATOR ",") AS words \
                                     FROM (SELECT rw.rule_id, rw.word_seq, rw.word_id \
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
    'get_sentence_words_rnum'   :   'SELECT r.rnum as sentence_id, t.word_seqs, t.word_ids \
                                     FROM (%s) AS t \
                                     JOIN (%s) AS r \
                                     ON t.post_id = r.post_id AND t.sentence_seq = r.sentence_seq'
    }


# Should be modified when it be deployed.
def connect_db():
    conn = mdb.connect(host='localhost', user='root', passwd='', db='morpheme')
    return conn

def connect_redis():
    rd = redis.StrictRedis(host='localhost', port=6379, db=0)
    return rd

# Only execute at the first time.
def init_db():
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

def store_posts():
    db = connect_db()
    cur = db.cursor()

    cur.execute(queries['add_topic'], (u'총선', ))
    topic_id = cur.lastrowid
    cur.execute(queries['add_source'], ('naver', ))
    source_id = cur.lastrowid

    files = crawl()
    print files;
    for fname in files:
        f = open(fname)
        print 'inserting %s' %fname

        # insert post
        cur.execute(queries['add_post'], (topic_id, source_id, fname, 'dummy_url'))
        post_id = cur.lastrowid

        lines = convert_textfile_to_lines(f)
        sentences = do_sentencing_without_threading(lines)
        for i in range (len(sentences)):
            # insert sentence
            sentence = sentences[i]
            # sentence_with_br = sentence.strip() 
            # if len(sentence) != len(sentence_with_br):
                # sentence_with_br += '<br>'
            # cur.execute(queries['add_sentence'], (post_id, i, sentence_with_br))
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
def show_posts():
    cur = g.db.cursor()
    cur.execute(queries['get_topics'])
    topics = [dict(id=int(row[0]), name=row[1]) for row in cur.fetchall()]
    cur.execute(queries['get_sources'])
    sources = [dict(id=int(row[0]), name=row[1]) for row in cur.fetchall()]
    return render_template('show_posts.html', topics=topics, sources=sources)

@app.route('/_posts', methods=['GET'])
def posts():
    if request.method == 'GET':
        topic = ast.literal_eval(request.args.get('topic'))
        sources_ids = ast.literal_eval(request.args.get('sources'))
        format_string = ', '.join(['%s']*len(sources_ids))
        db = g.db
        cur = db.cursor()

        cur.execute(queries['get_posts'] %('%s', format_string), [topic] + sources_ids)
        posts = [dict(id=int(row[0]), title=row[1], url=row[2]) for row in cur.fetchall()]

        cur.execute(queries['get_rulesets'], (topic, ))
        # rulesets = [dict(category_seq=int(row[0]), name=row[1]) for row in cur.fetchall()]
        rulesets = []
        category_seqs = []
        for row in cur.fetchall():
            rulesets.append(dict(category_seq=int(row[0]), name=row[1]))
            category_seqs.append(int(row[0]))

        ruleset_rules_dic = {}
        for category_seq in category_seqs:
            cur.execute(queries['get_rules'], (topic, category_seq))
            rule_dic = {}
            for row in cur.fetchall():
                rule_id = int(row[0])
                full_text, word = row[1:]
                word = word[:word.rindex('_')]
                if rule_id not in rule_dic:
                    rule_dic[rule_id] = (full_text, [word])
                else:
                    rule_dic[rule_id][1].append(word)
            rules = [dict(rule_id=int(key), full_text=val[0], word=val[1]) for key, val in rule_dic.iteritems()]
            ruleset_rules_dic[category_seq] = rules

        rd = g.rd
        rule_count_dic = {key: rd.bitcount(key) for key in rd.keys()}
        return jsonify(posts=posts, rulesets=rulesets, ruleset_rules_dic=ruleset_rules_dic, rule_count_dic=rule_count_dic)

@app.route('/_sentences', methods=['GET'])
def sentences():
    if request.method == 'GET':
        cur = g.db.cursor()
        topic = ast.literal_eval(request.args.get('topic'))
        sources_ids = ast.literal_eval(request.args.get('sources'))
        format_string = ', '.join(['%s']*len(sources_ids))
        post_id = ast.literal_eval(request.args.get('post_id'))
        cur.execute(queries['get_sentences']%(queries['get_sentences_rnum'], '%s')%('%s', format_string, '%s'), \
                    [topic] + sources_ids + [post_id])
        rd = g.rd
        sentences = []
        for row in cur.fetchall():
            sentence_id = int(row[0])
            full_text = row[1]
            rules = []
            for key in rd.keys():
                try:
                    if rd.getbit(key, sentence_id) == 1:
                        rules.append(int(key))
                except:
                    pass
            sentences.append(dict(sentence_id=sentence_id, full_text=full_text, rules=rules))
        # sentences = [dict(sentence_id=row[0], full_text=row[1]) for row in cur.fetchall()]
        return jsonify(sentences=sentences)

@app.route('/_rulesets', methods=['POST', 'DELETE'])
def rulesets():
    if request.method == 'POST':
        topic = ast.literal_eval(request.form['topic'])
        name = request.form['name']
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
        db = g.db
        cur = db.cursor()
        cur.execute(queries['get_rules'], (topic, category_seq))
        rd = g.rd
        for row in cur.fetchall():
            rd.delete(int(row[0]))
        cur.execute(queries['del_rules_word_relations'], (topic, category_seq))
        cur.execute(queries['del_rules'], (topic, category_seq))
        cur.execute(queries['del_ruleset'], (topic, category_seq))
        db.commit()
        return jsonify(deleted=dict(topic=topic, category_seq=category_seq))


@app.route('/_parsing', methods=['GET'])
def parsing():
    jpype.attachThreadToJVM()
    text = request.args.get('text')
    return jsonify(morphs=do_parsing_without_threading(text))

@app.route('/_rules', methods=['POST', 'DELETE'])
def rules():
    db = g.db
    cur = db.cursor()

    if request.method == 'POST':
        topic = ast.literal_eval(request.form['topic'])
        category_seq = ast.literal_eval(request.form['category_seq'])
        ruleText = request.form['ruleText']
        checked = ast.literal_eval(request.form['checked'])
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
        rd = g.rd
        rd.delete(rule_id)
        cur.execute(queries['del_rule_word_relations'], (rule_id, ))
        cur.execute(queries['del_rule'], (rule_id, ))
        db.commit()
        return jsonify(deleted=dict(rule_id=rule_id))
    # if request.method == 'GET':
        # topic = ast.literal_eval(request.args.get('topic'))
        # category_seq = ast.literal_eval(request.args.get('category_seq'))
        # cur.execute(queries['get_rules'], (topic, category_seq))
        # rulesDic = {}
        # rule_count_dic = {}
        # for row in cur.fetchall():
            # rule_id = int(row[0])
            # full_text, word = row[1:]
            # word = word[:word.rindex('_')]
            # if rule_id not in rulesDic:
                # rulesDic[rule_id] = (full_text, [word])
                # rule_count_dic[str(rule_id)] = 0
            # else:
                # rulesDic[rule_id][1].append(word)
        # rules = [dict(rule_id=int(key), full_text=val[0], word=val[1]) for key, val in rulesDic.iteritems()]
        # rd = g.rd
        # for key in rd.keys():
            # rule_count_dic[key] = rd.bitcount(key)
        # print rule_count_dic
        # return jsonify(rules=rules, rule_count_dic=rule_count_dic)

# not used
def retrieve_sentence_ids(rd, key):
    ret = []
    while(True):
        pos = rd.bitpos(key, 1)
        if pos < 0: break
        ret.append(pos)
        rd.setbit(key, pos, 0)
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

@app.route('/_analysis', methods=['POST'])
def run():
    if request.method == 'POST':
        topic = ast.literal_eval(request.form['topic'])
        sources_ids = ast.literal_eval(request.form['sources'])
        source_format_string = ', '.join(['%s']*len(sources_ids))

        rd = g.rd
        rd.flushall()
        pipe = rd.pipeline()
        db = g.db
        cur = db.cursor()
        cur.execute(queries['get_rule_words'], (topic, ))

        rule_count_dic = {}
        valid_sentences = []
        for row_rule in cur.fetchall():
            rule_id = int(row_rule[0])
            pipe.setbit(rule_id, 0, 0)
            gap = int(row_rule[1])
            rule_word_ids = map(int, row_rule[2].split(','))
            rule_word_id_format_string = ', '.join(['%s']*len(rule_word_ids))
            cur.execute(queries['get_sentence_words_rnum']%(queries['get_sentence_words'], queries['get_sentences_rnum'])
                                                           %('%s', source_format_string, rule_word_id_format_string, rule_word_id_format_string, '%s', \
                                                             '%s', source_format_string),
                        [topic] + sources_ids + rule_word_ids + rule_word_ids + [len(rule_word_ids)] + [topic] + sources_ids)
            del valid_sentences[:]
            for row_sentence in cur.fetchall():
                sentence_id = int(row_sentence[0])
                word_seqs = map(int, row_sentence[1].split(','))
                sentence_word_ids = map(int, row_sentence[2].split(','))
                if is_valid_sentences(gap, rule_word_ids, word_seqs, sentence_word_ids):
                    valid_sentences.append(sentence_id)
            for sentence_id in valid_sentences:
                pipe.setbit(rule_id, sentence_id, 1)
            rule_count_dic[rule_id] = len(valid_sentences)
        pipe.execute()
    return jsonify(rule_count_dic=rule_count_dic)

if __name__ == '__main__':
    # init_db()
    # store_posts()
    # build_redis()
    app.run(debug=True)
    # pass

