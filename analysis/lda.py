# -*- coding: utf-8 -*-
from time import time
import os
import csv
import multiprocessing
import click
from gensim import corpora
from gensim.models.ldamulticore import LdaMulticore
from helpers import Utils


class LdaUtils(Utils):
    NECESSARIES = [u'Noun', u'Adverb', u'Adjective', u'Verb']

    @staticmethod
    def filter_rec(func, iterable):
        ret = []
        for item in iterable:
            if type(item) == list:
                ret.append(Utils.filter_rec(func, item))
            else:
                if func(item):
                    ret.append(item)
        return ret

    @staticmethod
    def filter_words(words):
        return Utils.filter_rec(lambda x: x.split('_')[-1] in LdaUtils.NECESSARIES, words)

    @staticmethod
    def human_readable_time(s):
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return "%d : %02d : %02d" % (h, m, s)


class Lda(object):
    def __init__(self, **kwargs):
        self.DIR = kwargs.get('dir', '')
        self.words_fname = kwargs.get('words', '')
        self.id2word_fname = ''
        self.id2word = None
        self.corpus_fname = ''
        self.corpus = None
        self.model = None
        self.datafile = ''

    def __dest(self, path):
        return os.path.join(self.DIR, path)

    def build_id2word(self, fname=None, save_to=None):
        # read words.csv file
        if not fname:
            fname = self.words_fname or click.prompt('words file')
        fname = self.__dest(fname)
        assert os.path.isfile(fname), 'No such file: %s' % fname
        if save_to:
            self.id2word_fname = self.__dest(save_to)
        else:
            self.id2word_fname = LdaUtils.change_ext(fname, 'id2word')
        # if there is no id2word file or the user wants to rebuild, build .id2word
        if not os.path.isfile(self.id2word_fname) or click.confirm('There alread is id2word. Do you want to rebuild?'):
            print 'start building id2word'
            start = time()
            id2word = corpora.Dictionary(LdaUtils.filter_words(LdaUtils.iter_csv(fname, -1).split()))
            id2word.save(self.id2word_fname)  # save
            print 'building id2word takes: %s' % LdaUtils.human_readable_time(time() - start)
        self.id2word = corpora.Dictionary.load(self.id2word_fname)
        return self.id2word

    def __iter_doc2bow(self, generator):
        id2word = self.id2word or self.build_id2word()
        for tokens in generator:
            yield id2word.doc2bow(tokens)

    def build_corpus(self, fname=None, save_to=None):
        # read sentences file
        if not fname:
            fname = click.prompt('sentences file')
        fname = self.__dest(fname)
        assert os.path.isfile(fname), 'No such file: %s' % fname
        if save_to:
            self.corpus_fname = self.__dest(save_to)
        else:
            self.corpus_fname = LdaUtils.change_ext(fname, 'corpus')
        # if there is no corpus file or the user wants to rebuild, build .corpus
        if not os.path.isfile(self.corpus_fname) or click.confirm('There already is corpus. Do you want to rebuild?'):
            print 'start building corpus'
            start = time()
            corpora.MmCorpus.serialize(self.corpus_fname, self.__iter_doc2bow(LdaUtils.iter_csv(fname, -1).split()))  # save
            print 'building corpus takes: %s' % LdaUtils.human_readable_time(time() - start)
        self.corpus = corpora.MmCorpus(self.corpus_fname)
        return self.corpus

    def build_model(self, fname=None, save_to=None):
        id2word = self.id2word or self.build_id2word()
        corpus = self.corpus or self.build_corpus()
        # read model.lda file
        if not fname:
            fname = click.prompt('model file name', type=str, default='model.lda')
        fname = self.__dest(fname)
        # if there is no model file or the user wants to rebuild, build .model
        if not os.path.isfile(fname) or click.confirm('There already is %s. Do you want to re run lda?' % fname):
            num_procs = click.prompt('Number of processes to launch',
                                     type=int,
                                     default=multiprocessing.cpu_count())
            num_epochs = click.prompt('Number of epochs to run', type=int, default=20)
            num_topics = click.prompt('Number of topics', type=int, default=100)
            print 'start building model'
            start = time()
            model = LdaMulticore(corpus, id2word=id2word, num_topics=num_topics, workers=num_procs, passes=num_epochs)
            model.save(fname) #save
            print 'building model takes: %s' % LdaUtils.human_readable_time(time() - start)
        self.model = LdaMulticore.load(fname)
        return self.model

    def query_tag(self, words):
        id2word = self.id2word or self.build_id2word(self.datafile)
        model = self.model or self.build_model(self.datafile)
        bow = id2word.doc2bow(words)
        if len(bow) == 0:
            return None
        gamma, _ = model.inference([bow])
        topic_dist = gamma[0] / sum(gamma[0])
        return topic_dist

    def assign(self, datafile=None, outputfile=None):
        if not datafile:
            datafile = click.prompt('Data file',
                                    type=str,
                                    default='sentences_all.csv')
        datafile = self.__dest(datafile)
        self.datafile = datafile
        if not outputfile:
            datafilename, ext = os.path.splitext(datafile)
            default_outputfile = datafilename+'_result'+ext
            outputfile = click.prompt('output file',
                                      type=str,
                                      default=default_outputfile)
        assert os.path.isfile(datafile), 'No such file: %s' % datafile
        print 'start assiging'
        start = time()
        with open(datafile) as fi, open(outputfile, 'w') as fo:
            csv_reader = csv.reader(fi, delimiter=',')
            csv_writer = csv.writer(fo, delimiter=',')
            for row in csv_reader:
                out_row = row[:2]  # post_id and sentence_seq
                filtered_words = LdaUtils.filter_words(row[-1].split(' '))
                out_row.append(' '.join(map(str, self.query_tag(filtered_words))))
                csv_writer.writerow(out_row)
        print 'assigning takes: %s' % LdaUtils.human_readable_time(time() - start)


def main():
    lda = Lda(dir='')
    lda.build_id2word('./sentences_labeled.csv')
    lda.build_corpus('./sentences_unlabeled.csv', save_to='./sentences_unlabeled_with_labeled_words.corpus')
    # lda.build_model('model_all.lda')
    # lda.assign('sentences_all.csv')


if __name__ == '__main__':
    main()
