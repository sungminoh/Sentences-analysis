# -*- coding: utf-8 -*-
import MySQLdb as mdb
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
        'add_topic': 'INSERT INTO topics (name) VALUES (%s)',
        'get_topics': 'SELECT _id, name FROM topics',

        'add_source': 'INSERT INTO sources (name) VALUES (%s)',
        'get_sources': 'SELECT _id, name FROM sources',

        'add_post': 'INSERT INTO posts (topic_id, source_id, title, url) VALUES (%s, %s, %s, %s)',
        'add_sentence': 'INSERT INTO sentences (post_id, sentence_seq, full_text) VALUES (%s, %s, %s)',
        'add_word': 'INSERT IGNORE INTO words (word) VALUES (%s)',
        'add_sentence_word_relation': 'INSERT INTO sentence_word_relations (post_id, sentence_seq, word_seq, word_id) \
                        SELECT %s, %s, %s, _id FROM words WHERE word = %s',
        'get_posts': 'SELECT B._id, A.full_text FROM sentences AS A INNER JOIN posts AS B ON A.post_id = B._id \
                      WHERE B.topic_id = %s and B.source_id IN (%s)',

        'add_ruleset': 'INSERT INTO rulesets (topic_id, category_seq, name) \
                        SELECT %s, IFNULL(MAX(category_seq), 0) + 1, %s FROM rulesets WHERE topic_id = %s',
        'get_ruleset': 'SELECT category_seq, name FROM rulesets WHERE topic_id = %s ORDER BY category_seq DESC LIMIT 1',
        'get_rulesets': 'SELECT category_seq, name FROM rulesets WHERE topic_id = %s',
        'del_ruleset': 'DELETE FROM rulesets WHERE topic_id = %s and category_seq = %s',
        'del_rules': 'DELETE FROM rules WHERE topic_id = %s and category_seq = %s',
        'del_rules_word_relations': 'DELETE FROM rule_word_relations WHERE rule_id in (SELECT _id FROM rules WHERE  topic_id = %s and category_seq = %s)',

        'add_rule': 'INSERT INTO rules (topic_id, category_seq, full_text) VALUES (%s, %s, %s)',
        'get_rules': 'SELECT rule_id, full_text, word FROM rules AS A INNER JOIN rule_word_relations AS B ON A._id = B.rule_id INNER JOIN words AS C ON B.word_id = C._id WHERE A.topic_id = %s AND A.category_seq = %s',
        'del_rule': 'DELETE FROM rules WHERE _id = %s',
        'del_rule_word_relations': 'DELETE FROM rule_word_relations WHERE rule_id = %s',

        'add_rule_word_relation': 'INSERT INTO rule_word_relations (rule_id, word_seq, word_id) \
                                   SELECT %s, %s, _id FROM words WHERE word = %s'
            }


# Should be modified when it be deployed.
def connect_db():
    conn = mdb.connect(host='localhost', user='root', passwd='', db='morpheme')
    return conn

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

@app.teardown_request
def teardown_request(exception):
    g.db.close()

@app.route('/')
def show_posts():
    cur = g.db.cursor()
    cur.execute(queries['get_topics'])
    topics = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]
    cur.execute(queries['get_sources'])
    sources = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]
    return render_template('show_posts.html', topics=topics, sources=sources)

@app.route('/_posts', methods=['GET'])
def posts():
    if request.method == 'GET':
        topic = ast.literal_eval(request.args.get('topic'))
        sources_ids = ', '.join(list(map(lambda x: '%s' %x, ast.literal_eval(request.args.get('sources')))))
        cur = g.db.cursor()
        cur.execute(queries['get_posts'], (topic, sources_ids))
        posts = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
        cur.execute(queries['get_rulesets'], topic)
        rulesets = [dict(category_seq=row[0], name=row[1]) for row in cur.fetchall()]
        return jsonify(posts=posts, rulesets=rulesets)

@app.route('/_rulesets', methods=['POST', 'DELETE'])
def rulesets():
    if request.method == 'POST':
        topic = request.form['topic']
        name = request.form['name']
        db = g.db
        cur = db.cursor()
        cur.execute(queries['add_ruleset'], (topic, name, topic))
        db.commit()
        cur.execute(queries['get_ruleset'], (topic))
        rulesets = [dict(category_seq=row[0], name=row[1]) for row in cur.fetchall()]
        return jsonify(rulesets=rulesets)
    if request.method == 'DELETE':
        topic = request.form['topic']
        category_seq = request.form['category_seq']
        db = g.db
        cur = db.cursor()
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

@app.route('/_rules', methods=['GET', 'POST', 'DELETE'])
def rules():
    db = g.db
    cur = db.cursor()
    if request.method == 'POST':
        topic = request.form['topic']
        category_seq = request.form['category_seq']
        ruleText = request.form['ruleText']
        checked = ast.literal_eval(request.form['checked'])
        cur.executemany(queries['add_word'], map(tuplize, checked))
        cur.execute(queries['add_rule'], (topic, category_seq, ruleText))
        rule_id = cur.lastrowid
        for seq, word in enumerate(checked):
            cur.execute(queries['add_rule_word_relation'], (rule_id, seq+1, word))
        db.commit()
        return jsonify(checked=checked)
    if request.method == 'GET':
        topic = request.args.get('topic')
        category_seq = request.args.get('category_seq')
        cur.execute(queries['get_rules'], (topic, category_seq))
        rulesDic = {}
        for row in cur.fetchall():
            rule_id, full_text, word = row
            word = word[:word.rindex('_')]
            if rule_id not in rulesDic:
                rulesDic[rule_id] = (full_text, [word])
            else:
                rulesDic[rule_id][1].append(word)
        rules = [dict(rule_id=key, full_text=val[0], word=val[1]) for key, val in rulesDic.iteritems()]
        return jsonify(rules=rules)
    if request.method == 'DELETE':
        rule_id = request.form['rule_id']
        cur.execute(queries['del_rule_word_relations'], (rule_id, ))
        cur.execute(queries['del_rule'], (rule_id, ))
        db.commit()
        return jsonify(deleted=dict(rule_id=rule_id))
    
# @app.route('/add', methods=['POST'])
# def add_entry():
    # if not session.get('logged_in'):
        # abort(401)
    # db = g.db
    # cur = db.cursor()
    # cur.execute('INSERT INTO entries (title, text) VALUES (%s, %s)',
                 # [request.form['title'], request.form['text']])
    # db.commit()
    # flash('New entry was successfully posted')
    # return redirect(url_for('show_entries'))

# @app.route('/login', methods=['GET', 'POST'])
# def login():
    # error = None
    # if request.method == 'POST':
        # if request.form['username'] != app.config['USERNAME']:
            # error = 'Invalid username'
        # elif request.form['password'] != app.config['PASSWORD']:
            # error = 'Invalid password'
        # else:
            # session['logged_in'] = True
            # flash('you were logged in')
            # return redirect(url_for('show_entries'))
    # return render_template('login.html', error=error)

# @app.route('/logout')
# def logout():
    # session.pop('logged_in', None)
    # flash('you were logged out')
    # return redirect(url_for('show_entries'))

if __name__ == '__main__':
    # init_db()
    # store_posts()
    app.run(debug=True)
    # pass

