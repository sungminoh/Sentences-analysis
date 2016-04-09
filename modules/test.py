# -*- coding: utf-8 -*-
from konlpy.tag import Twitter 
from konlpy.tag import Kkma
from konlpy.utils import pprint 
from threading import Thread
import jpype
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

kkma = Kkma()
twitter = Twitter()

def convert_textfile_to_lines(f):
    lines = []
    while(True):
        line = f.readline()
        if not line: break
        line = u'%s' % line.strip()
        if line == '': continue
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
    jpype.detachThreadFromJVM()
    return sum(sum(result_sentencing_thread, []), [])

def do_sentencing_without_threading(lines):
    return sum([kkma.sentences(line) for line in lines], [])

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
    jpype.detachThreadFromJVM()
    return sum(result_parsing_thread, [])

def do_parsing_without_threading(sentences):
    return [twitter.morphs(sentence) for sentence in sentences]

if __name__=='__main__':
    result_sentencing_thread = []
    result_parsing_thread = []

    f = open('./dummy_article_03.txt')

    lines = convert_textfile_to_lines(f)

    sentences = do_sentencing_by_threading(lines)
    # sentences = do_sentencing_without_threading(lines)
    print "sentences"
    pprint(sentences)

    morphs = do_parsing_by_threading(sentences)
    # morphs = do_parsing_without_threading(sentences)
    print "morphs"
    pprint(morphs)

