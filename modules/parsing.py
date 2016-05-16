# -*- coding: utf-8 -*-
from konlpy.tag import Twitter 
from konlpy.tag import Kkma
from konlpy.utils import pprint 
from threading import Thread
from more_itertools import unique_everseen
import jpype
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

kkma = Kkma()
twitter = Twitter()

result_sentencing_thread = []
result_parsing_thread = []

def convert_textfile_to_lines(f):
    lines = []
    while(True):
        line = f.readline()
        if not line: break
        line = u'%s' % line
        if line.strip() == '': continue
        lines.append(line)
    return lines

def do_sentencing(start, end, lines, result_sentencing_thread):
    jpype.attachThreadToJVM()
    sentences = [kkma.sentences(lines[i]) for i in range(start, end)]
    result_sentencing_thread.append(sentences)
    return

def do_sentencing_by_threading(lines):
    nlines = len(lines)
    t1 = Thread(target=do_sentencing, args=(0, int(nlines/2), lines, result_sentencing_thread))
    t2 = Thread(target=do_sentencing, args=(int(nlines/2), nlines, lines, result_sentencing_thread))
    t1.start(); t2.start()
    t1.join(); t2.join()
    # jpype.detachThreadFromJVM()
    return sum(sum(result_sentencing_thread, []), [])

def do_sentencing_without_threading(lines):
    ret = []
    for line in lines:
        striped_line = line.strip()
        remainder = ''
        if len(line) != len(striped_line):
            remainder = line[len(striped_line):]
        sentences = kkma.sentences(line)
        sentences[-1] += remainder
        ret += sentences
    return ret

def do_parsing(start, end, sentences, result_parsing_thread):
    jpype.attachThreadToJVM()
    morphs = [twitter.morphs(sentences[i]) for i in range(start, end)]
    result_parsing_thread.append(morphs)
    return

def do_parsing_by_threading(sentences):
    nsentences = len(sentences)
    t1 = Thread(target=do_parsing, args=(0, int(nsentences/2), sentences, result_parsing_thread))
    t2 = Thread(target=do_parsing, args=(int(nsentences/2), nsentences, sentences, result_parsing_thread))
    t1.start(); t2.start()
    t1.join(); t2.join()
    # jpype.detachThreadFromJVM()
    return sum(result_parsing_thread, [])

def do_parsing_without_threading(sentences):
    if type(sentences) is list:
        return [twitter.pos(sentence) for sentence in sentences]
    else:
        jpype.attachThreadToJVM()
        return twitter.pos(sentences)

def dedup(l):
    return list(unique_everseen(l))

def concate_tuple(t):
    return '%s_%s' % t

    
if __name__=='__main__':

    f = open('./dummy_article_03.txt')

    lines = convert_textfile_to_lines(f)

    # sentences = do_sentencing_by_threading(lines)
    # sentences = do_sentencing_without_threading(lines)
    sentences = '[ 천지 일보= 임 문식 기자] 4.13 총선을 나흘 남겨 둔 9일 여야 정치권이 20대 총선 성패를 좌우할 수도권 등 전국 곳곳에서 표 심 잡기에 집중, 사활을 건 유세전을 펼쳤다.'
    print "sentences"
    pprint(sentences)


    # morphs = do_parsing_by_threading(sentences)
    morphs = do_parsing_without_threading(sentences)
    print "morphs"
    pprint(morphs)

    # morphs = [('a','1'), ('b','2')]
    morphs = map(concate_tuple, morphs)
    pprint(morphs)

