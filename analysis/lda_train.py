# -*- coding: utf-8 -*-

import os
import sys
import multiprocessing
import optparse
import csv
import re
import string
from unidecode import unidecode
from gensim import utils, corpora
from gensim.models.ldamulticore import LdaMulticore

csv.field_size_limit(sys.maxsize)
NUM_PROCS = int(multiprocessing.cpu_count() * 2.0 / 3.0)
if NUM_PROCS == 0:
  NUM_PROCS = 1

#EMOTICON_MASK = re.compile(u'(?<!&)#(\w|(?:[\xA9\xAE\u203C\u2049\u2122\u2139\u2194-\u2199\u21A9\u21AA\u231A\u231B\u2328\u2388\u23CF\u23E9-\u23F3\u23F8-\u23FA\u24C2\u25AA\u25AB\u25B6\u25C0\u25FB-\u25FE\u2600-\u2604\u260E\u2611\u2614\u2615\u2618\u261D\u2620\u2622\u2623\u2626\u262A\u262E\u262F\u2638-\u263A\u2648-\u2653\u2660\u2663\u2665\u2666\u2668\u267B\u267F\u2692-\u2694\u2696\u2697\u2699\u269B\u269C\u26A0\u26A1\u26AA\u26AB\u26B0\u26B1\u26BD\u26BE\u26C4\u26C5\u26C8\u26CE\u26CF\u26D1\u26D3\u26D4\u26E9\u26EA\u26F0-\u26F5\u26F7-\u26FA\u26FD\u2702\u2705\u2708-\u270D\u270F\u2712\u2714\u2716\u271D\u2721\u2728\u2733\u2734\u2744\u2747\u274C\u274E\u2753-\u2755\u2757\u2763\u2764\u2795-\u2797\u27A1\u27B0\u27BF\u2934\u2935\u2B05-\u2B07\u2B1B\u2B1C\u2B50\u2B55\u3030\u303D\u3297\u3299]|\uD83C[\uDC04\uDCCF\uDD70\uDD71\uDD7E\uDD7F\uDD8E\uDD91-\uDD9A\uDE01\uDE02\uDE1A\uDE2F\uDE32-\uDE3A\uDE50\uDE51\uDF00-\uDF21\uDF24-\uDF93\uDF96\uDF97\uDF99-\uDF9B\uDF9E-\uDFF0\uDFF3-\uDFF5\uDFF7-\uDFFF]|\uD83D[\uDC00-\uDCFD\uDCFF-\uDD3D\uDD49-\uDD4E\uDD50-\uDD67\uDD6F\uDD70\uDD73-\uDD79\uDD87\uDD8A-\uDD8D\uDD90\uDD95\uDD96\uDDA5\uDDA8\uDDB1\uDDB2\uDDBC\uDDC2-\uDDC4\uDDD1-\uDDD3\uDDDC-\uDDDE\uDDE1\uDDE3\uDDEF\uDDF3\uDDFA-\uDE4F\uDE80-\uDEC5\uDECB-\uDED0\uDEE0-\uDEE5\uDEE9\uDEEB\uDEEC\uDEF0\uDEF3]|\uD83E[\uDD10-\uDD18\uDD80-\uDD84\uDDC0]|(?:0\u20E3|1\u20E3|2\u20E3|3\u20E3|4\u20E3|5\u20E3|6\u20E3|7\u20E3|8\u20E3|9\u20E3|#\u20E3|\\*\u20E3|\uD83C(?:\uDDE6\uD83C(?:\uDDEB|\uDDFD|\uDDF1|\uDDF8|\uDDE9|\uDDF4|\uDDEE|\uDDF6|\uDDEC|\uDDF7|\uDDF2|\uDDFC|\uDDE8|\uDDFA|\uDDF9|\uDDFF|\uDDEA)|\uDDE7\uD83C(?:\uDDF8|\uDDED|\uDDE9|\uDDE7|\uDDFE|\uDDEA|\uDDFF|\uDDEF|\uDDF2|\uDDF9|\uDDF4|\uDDE6|\uDDFC|\uDDFB|\uDDF7|\uDDF3|\uDDEC|\uDDEB|\uDDEE|\uDDF6|\uDDF1)|\uDDE8\uD83C(?:\uDDF2|\uDDE6|\uDDFB|\uDDEB|\uDDF1|\uDDF3|\uDDFD|\uDDF5|\uDDE8|\uDDF4|\uDDEC|\uDDE9|\uDDF0|\uDDF7|\uDDEE|\uDDFA|\uDDFC|\uDDFE|\uDDFF|\uDDED)|\uDDE9\uD83C(?:\uDDFF|\uDDF0|\uDDEC|\uDDEF|\uDDF2|\uDDF4|\uDDEA)|\uDDEA\uD83C(?:\uDDE6|\uDDE8|\uDDEC|\uDDF7|\uDDEA|\uDDF9|\uDDFA|\uDDF8|\uDDED)|\uDDEB\uD83C(?:\uDDF0|\uDDF4|\uDDEF|\uDDEE|\uDDF7|\uDDF2)|\uDDEC\uD83C(?:\uDDF6|\uDDEB|\uDDE6|\uDDF2|\uDDEA|\uDDED|\uDDEE|\uDDF7|\uDDF1|\uDDE9|\uDDF5|\uDDFA|\uDDF9|\uDDEC|\uDDF3|\uDDFC|\uDDFE|\uDDF8|\uDDE7)|\uDDED\uD83C(?:\uDDF7|\uDDF9|\uDDF2|\uDDF3|\uDDF0|\uDDFA)|\uDDEE\uD83C(?:\uDDF4|\uDDE8|\uDDF8|\uDDF3|\uDDE9|\uDDF7|\uDDF6|\uDDEA|\uDDF2|\uDDF1|\uDDF9)|\uDDEF\uD83C(?:\uDDF2|\uDDF5|\uDDEA|\uDDF4)|\uDDF0\uD83C(?:\uDDED|\uDDFE|\uDDF2|\uDDFF|\uDDEA|\uDDEE|\uDDFC|\uDDEC|\uDDF5|\uDDF7|\uDDF3)|\uDDF1\uD83C(?:\uDDE6|\uDDFB|\uDDE7|\uDDF8|\uDDF7|\uDDFE|\uDDEE|\uDDF9|\uDDFA|\uDDF0|\uDDE8)|\uDDF2\uD83C(?:\uDDF4|\uDDF0|\uDDEC|\uDDFC|\uDDFE|\uDDFB|\uDDF1|\uDDF9|\uDDED|\uDDF6|\uDDF7|\uDDFA|\uDDFD|\uDDE9|\uDDE8|\uDDF3|\uDDEA|\uDDF8|\uDDE6|\uDDFF|\uDDF2|\uDDF5|\uDDEB)|\uDDF3\uD83C(?:\uDDE6|\uDDF7|\uDDF5|\uDDF1|\uDDE8|\uDDFF|\uDDEE|\uDDEA|\uDDEC|\uDDFA|\uDDEB|\uDDF4)|\uDDF4\uD83C\uDDF2|\uDDF5\uD83C(?:\uDDEB|\uDDF0|\uDDFC|\uDDF8|\uDDE6|\uDDEC|\uDDFE|\uDDEA|\uDDED|\uDDF3|\uDDF1|\uDDF9|\uDDF7|\uDDF2)|\uDDF6\uD83C\uDDE6|\uDDF7\uD83C(?:\uDDEA|\uDDF4|\uDDFA|\uDDFC|\uDDF8)|\uDDF8\uD83C(?:\uDDFB|\uDDF2|\uDDF9|\uDDE6|\uDDF3|\uDDE8|\uDDF1|\uDDEC|\uDDFD|\uDDF0|\uDDEE|\uDDE7|\uDDF4|\uDDF8|\uDDED|\uDDE9|\uDDF7|\uDDEF|\uDDFF|\uDDEA|\uDDFE)|\uDDF9\uD83C(?:\uDDE9|\uDDEB|\uDDFC|\uDDEF|\uDDFF|\uDDED|\uDDF1|\uDDEC|\uDDF0|\uDDF4|\uDDF9|\uDDE6|\uDDF3|\uDDF7|\uDDF2|\uDDE8|\uDDFB)|\uDDFA\uD83C(?:\uDDEC|\uDDE6|\uDDF8|\uDDFE|\uDDF2|\uDDFF)|\uDDFB\uD83C(?:\uDDEC|\uDDE8|\uDDEE|\uDDFA|\uDDE6|\uDDEA|\uDDF3)|\uDDFC\uD83C(?:\uDDF8|\uDDEB)|\uDDFD\uD83C\uDDF0|\uDDFE\uD83C(?:\uDDF9|\uDDEA)|\uDDFF\uD83C(?:\uDDE6|\uDDF2|\uDDFC))))[\ufe00-\ufe0f\u200d]?)+',re.UNICODE)
try:
  # UCS-4
  EMOTICON = re.compile(u'([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])')
except Exception, e:
  # UCS-2
  EMOTICON = re.compile(u'([\u2600-\u27BF])|([\uD83C][\uDF00-\uDFFF])|([\uD83D][\uDC00-\uDE4F])|([\uD83D][\uDE80-\uDEFF])')

PUNCTUATION = re.compile('[%s]' % re.escape(string.punctuation))
WHITESPACE = re.compile(r'\s+')


def log(msg):
  sys.stdout.write(msg+'\n')
  sys.stdout.flush()


def make_cli_parser():
  """Make the command line interface parser."""
  usage = "\n\n".join(["python INPUT_CSV MODEL_PATH",
"""
ARGUMENTS:
  INPUT_CSV: an input file with rows of documents
  MODEL_PATH: an output file\
"""])
  cli_parser = optparse.OptionParser(usage)
  cli_parser.add_option('-n', '--numprocs', type='int',
          default=NUM_PROCS,
          help="Number of processes to launch [DEFAULT: %default]")
  cli_parser.add_option('-l', '--numlines', type='int',
          default=15000*5,
          help="Number of lines to read. -1 means unlimited [DEFAULT: %default]")
  cli_parser.add_option('-e', '--numepochs', type='int',
          default=20,
          help="Number of epochs to run [DEFAULT: %default]")
  cli_parser.add_option('-t', '--numtopics', type='int',
          default=100,
          help="Number of topics to generate [DEFAULT: %default]")
  return cli_parser


def preprocess(post):
  # example
  # {(romeo and juliet 2013),(romeo and juliet),(douglas booth),(hailee steinfeld)}"
  # -> romeo and juliet 2013 romeo and juliet douglas booth hailee steinfeld
  print post
  # remove all punctuations
  post = PUNCTUATION.sub(' ', utils.to_unicode(post))

  # replace all emoji characters to '_EMOTICON_' and add space in between.
  post = EMOTICON.sub(' _emoticon_ ', post)
  
  # convert all special characters to ascii characters
  post = unidecode(post).decode('ascii', 'ignore')
  
  # remove all whitespace into single one
  post = WHITESPACE.sub(' ', post).strip()
  return utils.to_unicode(post)


def iter_file(path, max_lines):
  counter = 0
  infile = open(path)
  in_csvfile = csv.reader(infile, delimiter=',')
  for row in in_csvfile:
    if max_lines > 0 and counter >= max_lines:
      break
    print len(row), row
    processed_post = preprocess(row[3]).split()
    if len(processed_post) == 0: # skip 0~2 word documents (quite useless)
      continue
    counter += 1
    yield processed_post
  infile.close()


def iter_doc2bow(path, max_lines, id2word):
  for tokens in iter_file(path, max_lines):
  	yield id2word.doc2bow(tokens)


def query_tag(id2word, model, split_word):
  # id2word = corpora.Dictionary.load(path+'.id2word')
  # model = LdaMulticore.load(path+'.lda')
  bow = id2word.doc2bow(split_word)
  if len(bow) == 0:
  	return None
  gamma, _ = model.inference([bow])
  topic_dist = gamma[0] / sum(gamma[0])  # normalize distribution
  # [(topicid, topicvalue) for topicid, topicvalue in enumerate(topic_dist)]
  return topic_dist


def main(argv):
  cli_parser = make_cli_parser()
  opts, args = cli_parser.parse_args(argv)
  if len(args) != 2:
    cli_parser.error("Please provide an input/output file")
  
  if not os.path.isfile(args[1]+'.lda'):
    if os.path.isfile(args[1]+'.bow2mm') and os.path.isfile(args[1]+'.id2word'):
      id2word = corpora.Dictionary.load(args[1]+'.id2word')
    else :
      id2word = corpora.Dictionary(iter_file(args[0], opts.numlines))
      # ignore words that appear in less than 5 documents or more than 20% documents
      # when we do filtering, some vector becomes empty! it generates a huge problem!!
      # id2word.filter_extremes(no_below=5, no_above=0.2, keep_n=None)
      # save dictionary
      id2word.save(args[1]+'.id2word')
      # save doc2bow vector
      corpora.MmCorpus.serialize(args[1]+'.bow2mm', iter_doc2bow(args[0], opts.numlines, id2word))
    mm_corpus = corpora.MmCorpus(args[1]+'.bow2mm')
    model=LdaMulticore(mm_corpus, id2word=id2word, num_topics=opts.numtopics, workers=opts.numprocs, passes=opts.numepochs)
    model.save(args[1]+'.lda')

  infile = open(args[0])
  outfile = open(args[1]+'.csv', "w")
  out_csvfile = csv.writer(outfile, delimiter =',')
  in_csvfile = csv.reader(infile, delimiter=',')
  for row in in_csvfile:
    if row[0] == 0:
      break
    processed_post = preprocess(row[3]).split()
    if len(processed_post) == 0: # skip 0~2 word documents (quite useless)
      continue
    result_list = row[1:3]
    result_list.extend(query_tag(id2word, model, processed_post))
    out_csvfile.writerow(result_list)
  infile.close()
  outfile.close()

  #print query_tag(id2word, model, "Hello über, world is awesome!")

if __name__ == '__main__':
    main(sys.argv[1:])