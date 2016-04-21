# -*- coding: utf-8 -*-
import MySQLdb as mdb
import _mysql_exceptions
import sys
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
    files = crawl()
    print files;
    for fname in files:
        cur = db.cursor()
        f = open(fname)
        print 'inserting %s' %fname

        # insert post
        add_post = 'INSERT INTO posts (url, title) VALUES (%s, %s)'
        cur.execute(add_post, ('dummy', fname))
        post_id = cur.lastrowid

        lines = convert_textfile_to_lines(f)
        sentences = do_sentencing_without_threading(lines)
        for i in range (len(sentences)):
            sentence = sentences[i]
            # insert sentence
            add_sentence = 'INSERT INTO sentences (post_id, sentence_seq, full_text) VALUES (%s, %s, %s)'
            cur.execute(add_sentence, (post_id, i, sentence))

            morphs = map(concate_tuple, do_parsing_without_threading(sentence))
            morphs_dedup = map(tuplize, dedup(morphs)) # can be ignored. need to check
            
            # insert newly appeared words. if there already is, idk, maybe no inserting
            add_word = 'INSERT IGNORE INTO words (word) VALUES (%s)'
            cur.executemany(add_word, morphs_dedup)

            
            for j in range(len(morphs)):
                add_relation = 'INSERT INTO sentence_word_relations (post_id, sentence_seq, word_seq, word_id) \
                                SELECT %s, %s, %s, _id FROM words WHERE word = %s'
                cur.execute(add_relation, (post_id, i, j, morphs[j]))

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
    cur.execute('select post_id, full_text from sentences')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('show_posts.html', entries=entries)

@app.route('/parsing', methods=['GET'])
def parsing():
    jpype.attachThreadToJVM()
    text = request.args.get('text')
    return jsonify(result=do_parsing_without_threading(text))
    
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = g.db
    cur = db.cursor()
    cur.execute('insert into entries (title, text) values (%s, %s)',
                 [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('you were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('you were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    # init_db()
    # store_posts()
    app.run(debug=True)
    # pass

