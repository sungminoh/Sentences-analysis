# -*- coding: utf-8 -*-
from time import time
import os
import csv
import multiprocessing
import click
from gensim import corpora
from gensim.models.ldamulticore import LdaMulticore


NECESSARIES = [u'Noun', u'Adverb', u'Adjective', u'Verb']


def iter_csv(path, nth):
    with open(path) as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            yield row[nth].split()


def filter_rec(func, iterable):
    ret = []
    for item in iterable:
        if type(item) == list:
            ret.append(filter_rec(func, item))
        else:
            if func(item):
                ret.append(item)
    return ret


def filter_words(words):
    return filter_rec(lambda x: x.split('_')[-1] in NECESSARIES, words)


def build_id2word(words=None):
    if words is None:
        words = click.prompt('word file')
    assert os.path.isfile(words), 'No such file'
    fname, _ = os.path.splitext(words)
    id2word_fname = fname+'.id2word'
    if os.path.isfile(id2word_fname):
        if not click.confirm('There alread is id2word. Do you want to rebuild?'):
            print 'load'
            return corpora.Dictionary.load(id2word_fname)
    id2word = corpora.Dictionary(filter_words(iter_csv(words, -1)))
    id2word.save(id2word_fname)
    print 'done'
    return id2word


def iter_doc2bow(generator, id2word):
    for tokens in generator:
        yield id2word.doc2bow(tokens)


def build_corpus(id2word, doc):
    if doc is None:
        doc = click.prompt('sentence file')
    assert os.path.isfile(doc), 'No such file'
    fname, _ = os.path.splitext(doc)
    doc2mm_fname = fname+'.doc2mm'
    if os.path.isfile(doc2mm_fname):
        if not click.confirm('There already is doc2mm. Do you want to rebuild?'):
            return corpora.MmCorpus(doc2mm_fname)
    corpora.MmCorpus.serialize(doc2mm_fname, iter_doc2bow(iter_csv(doc, -1), id2word))
    return corpora.MmCorpus(doc2mm_fname)


def build_model(id2word, mmcorpus, fname=None):
    if fname is None:
        fname = click.prompt('model file name',
                             type=str,
                             default='model.lda')
    if os.path.isfile(fname):
        if not click.confirm('There already is %s. Do you want to re run lda?' % fname):
            return LdaMulticore.load(fname)
    numprocs = click.prompt('Number of processes to launch',
                            type=int,
                            default=multiprocessing.cpu_count())
    numepochs = click.prompt('Number of epochs to run',
                             type=int,
                             default=20)
    model = LdaMulticore(mmcorpus, id2word=id2word, num_topics=100, workers=numprocs, passes=numepochs)
    model.save(fname)
    print 'done'
    return model


def query_tag(id2word, model, words):
    bow = id2word.doc2bow(words)
    if len(bow) == 0:
        return None
    gamma, _ = model.inference([bow])
    topic_dist = gamma[0] / sum(gamma[0])
    return topic_dist


def assign(id2word, model, datafile=None, outputfile=None):
    if datafile is None:
        datafile = click.prompt('Data file',
                                type=str,
                                default='./csv/sentences_data.csv')
    if outputfile is None:
        datafilename, ext = os.path.splitext(datafile)
        default_outputfile = datafilename+'_result'+ext
        outputfile = click.prompt('output file',
                                  type=str,
                                  default=default_outputfile)
    assert os.path.isfile(datafile), 'No such file'
    with open(datafile) as fi, open(outputfile, 'w') as fo:
        csv_reader = csv.reader(fi, delimiter=',')
        csv_writer = csv.writer(fo, delimiter=',')
        for row in csv_reader:
            out_row = row[:2]  # post_id and sentence_seq
            filtered_words = filter_words(row[-1].split(' '))
            out_row.append(' '.join(map(str, query_tag(id2word, model, filtered_words))))
            csv_writer.writerow(out_row)


def human_readable_time(s):
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return "%d : %02d : %02d" % (h, m, s)


def main():
    id2word = build_id2word('./csv/sentences_train.csv')
    mmcorpus = build_corpus(id2word, './csv/sentences_train.csv')
    model = build_model(id2word, mmcorpus, './csv/model.lda')
    start = time()
    assign(id2word, model, './csv/sentences_train.csv')
    mid = time()
    print "Takes: ", human_readable_time(mid - start)
    assign(id2word, model, './csv/sentences_data.csv')
    end = time()
    print "Takes: ", human_readable_time(end - mid)


if __name__ == '__main__':
    main()
