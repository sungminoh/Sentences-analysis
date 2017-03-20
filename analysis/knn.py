from gensim import corpora
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
from helpers import Utils, Progress


class CorpusKnn(object):
    classifier = None
    corpus = None
    coordinates = None
    labels = None
    data = None

    def __init__(self, corpus=None, label=None):
        if corpus:
            self.set_corpus(corpus)
        if self.corpus:
            self.corpus_to_coordinates()
        if label:
            self.set_labels(label)
        if self.coordinates is not None and self.labels is not None:
            self.build_classifier()

    @Utils.process
    def set_corpus(self, corpus):
        if isinstance(corpus, str):
            self.corpus = corpora.MmCorpus(corpus)
        elif isinstance(corpus, corpora.MmCorpus):
            self.corpus = corpus

    @Utils.process
    def set_data(self, corpus):
        if isinstance(corpus, str):
            self.data = corpora.MmCorpus(corpus)
        elif isinstance(corpus, corpora.MmCorpus):
            self.data = corpus

    @Utils.process
    def set_labels(self, sentences_csv_fname):
        self.labels = [int(x[0]) for x in Utils.iter_csv(sentences_csv_fname, 2).split()]
        return True

    @staticmethod
    def corpus_to_vector_generator(corpus):
        for sentence_corpus in corpus:
            vector = np.zeros(corpus.num_terms)
            for index, value in sentence_corpus:
                vector[index] = value
            yield vector

    @Utils.process
    def corpus_to_coordinates(self):
        self.coordinates = np.array(list(self.corpus_to_vector_generator(self.corpus)))

    @Utils.process
    def build_classifier(self):
        self.classifier = KNeighborsClassifier(n_neighbors=1)
        self.classifier.fit(self.coordinates, self.labels)

    def predict(self, vector):
        return self.classifier.predict(vector)[0]

    def predict_all_generator(self, corpus):
        if not self.data:
            self.set_data(corpus)
        for vector in self.corpus_to_vector_generator(self.data):
            yield self.predict(vector.reshape(1, -1))

    def predict_all(self, corpus):
        if not self.data:
            self.set_data(corpus)
        self.predictions = np.zeros(len(self.data))
        for i, prediction in enumerate(Progress(self.predict_all_generator(corpus), len(self.data), 10)):
            self.predictions[i] = prediction
        return self.predictions

    def save(self, fname):
        np.savetxt(fname, self.predictions, delimiter=',', fmt='%d')


def main():
    corpusKnn = CorpusKnn('./sentences_labeled.corpus', './sentences_labeled.csv')
    corpusKnn.predict_all('./sentences_unlabeled_with_labeled_words.corpus')
    corpusKnn.save('./sentences_unlabeled_assigned.txt')


if __name__ == '__main__':
    main()

