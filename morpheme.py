import MySQLdb as mdb
import _mysql_exceptions
import sys
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

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
                    cursor.execute(query)
                    query = ''
    db.close()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

@app.route('/')
def show_entries():
    cur = g.db.cursor()
    cur.execute('select title, text from entries order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)

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
    app.run(debug=True)

