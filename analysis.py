import MySQLdb as mdb
import _mysql_exceptions
import redis
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from modules.crawling import crawl
from database_info import mysql_info, redis_info
from time import strftime, time, sleep

flogname = './logs/analysis.log'

queries = {
    'get_max_post'              :   'SELECT MAX(_id) FROM posts',

    'get_max_post_by_cond'      :   'SELECT MAX(_id) FROM posts WHERE topic_id = %s AND source_id IN (%s)',

    'get_rule_words'            :   'SELECT category_seq, rule_id, (MAX(word_seq) - MIN(word_seq)) AS gap, GROUP_CONCAT(word_id ORDER BY word_seq SEPARATOR ",") AS words \
                                     FROM (SELECT r.category_seq, rw.rule_id, rw.word_seq, rw.word_id \
                                           FROM rule_word_relations AS rw \
                                           JOIN rules AS r ON r._id = rw.rule_id \
                                           ORDER BY word_seq) AS t \
                                     GROUP BY rule_id',

    'get_sentence_words'        :   'SELECT t1.post_id, t1.sentence_seq, GROUP_CONCAT(word_seq ORDER BY word_seq SEPARATOR ",") AS word_seqs, \
                                            GROUP_CONCAT(word_id ORDER BY word_seq SEPARATOR ",") AS word_ids \
                                     FROM (SELECT s.post_id, s.sentence_seq, r.word_seq, r.word_id FROM sentences AS s \
                                           JOIN sentence_word_relations AS r ON s.post_id = r.post_id AND s.sentence_seq = r.sentence_seq \
                                           JOIN (SELECT * FROM posts WHERE _id > %s AND _id < %s) AS p ON p._id = s.post_id \
                                           WHERE r.word_id IN (%s) ORDER BY word_seq) AS t1 \
                                     JOIN (SELECT s.post_id, s.sentence_seq, COUNT(*) AS cat_count \
                                           FROM sentences AS s \
                                           JOIN sentence_word_relations AS r ON s.post_id = r.post_id AND s.sentence_seq = r.sentence_seq \
                                           WHERE r.word_id IN (%s) \
                                           GROUP BY s.post_id, s.sentence_seq having cat_count >= %s) AS t2 \
                                     ON t1.post_id = t2.post_id AND t1.sentence_seq = t2.sentence_seq \
                                     GROUP BY post_id, sentence_seq',

    'insert_result'             :   'INSERT IGNORE INTO rule_sentence_relations (rule_id, post_id, sentence_seq)\
                                     VALUES (%s, %s, %s)'
}

def connect_db():
    return mdb.connect(**mysql_info())

def connect_rd():
    rd = redis.StrictRedis(**redis_info())
    return rd

def get_time():
    return strftime('%Y-%m-%d %H:%M:%S')

def logging(text):
    with open(flogname, 'a') as log: log.write(('[%s] ' % get_time()) + text + '\n')


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


def formatstring(arr):
    if type(arr) == list:
        return ', '.join(['%s']*len(arr))
    else:
        return '%s'


def get_post_until(topic=None, sources_ids=None):
    format_string = '%s'
    if sources_ids:
        format_string = formatstring(sources_ids)
    with connect_db() as cur:
        if topic:
            cur.execute(queries['get_max_post_by_cond'] % ('%s', format_string), [topic]+sources_ids)
        else:
            cur.execute(queries['get_max_post'])
        post_until = int(cur.fetchall()[0][0])
        return post_until


def get_rule_words():
    with connect_db() as cur:
        cur.execute(queries['get_rule_words'])
        return cur.fetchall()


def analyze(topic=None, sources_ids=None):
    cputime = time()

    post_until = get_post_until(topic, sources_ids)

    for row_rule in get_rule_words():
        rd = connect_rd()
        db = connect_db()
        cur = db.cursor()
        category_seq = int(row_rule[0])
        rule_id = int(row_rule[1])
        gap = int(row_rule[2])
        rule_word_ids = map(int, row_rule[3].split(','))
        rule_word_id_format_string = formatstring(rule_word_ids)

        last_post_id = 0
        if rd.exists(rule_id):
            last_post_id = int(rd.get(rule_id))

        cur.execute(queries['get_sentence_words']\
                    %('%s', '%s', rule_word_id_format_string, rule_word_id_format_string, '%s'),\
                    [last_post_id, post_until] + rule_word_ids + rule_word_ids + [len(rule_word_ids)])

        for row_sentence in cur.fetchall():
            post_id = int(row_sentence[0])
            sentence_seq = int(row_sentence[1])
            word_seqs = map(int, row_sentence[2].split(','))
            sentence_word_ids = map(int, row_sentence[3].split(','))
            if is_valid_sentences(gap, rule_word_ids, word_seqs, sentence_word_ids):
                cur.execute(queries['insert_result'], (rule_id, post_id, sentence_seq))

        db.commit()
        db.close()
        post_until = max(post_until, last_post_id)
        rd.set(rule_id, post_until)
        logging ('rule(%s) post(%s, %s) takes %s'\
                 % (str(rule_id), str(last_post_id), str(post_until), str(time()-cputime)))
    logging ('run until post_id %s, takes %s seconds' % (post_until, str(time()-cputime)))

if __name__ == '__main__':
    while(True):
        logging ('analyze start!!!')
        analyze()
        logging ('sleep')
        sleep(60*20)

