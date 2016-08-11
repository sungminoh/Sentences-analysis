# coding: utf-8

import tweepy as tw
import traceback
from time import strftime, sleep
import os
from twitter_keys import get_access_token, get_access_token_secret, get_consumer_key, get_consumer_secret

access_token = get_access_token()
access_token_secret = get_access_token_secret()
consumer_key = get_consumer_key()
consumer_secret = get_consumer_secret()
flogname = './log/crawl.log'
destdir = './posts/posts_08'

def logging(text):
    with open(flogname, 'a') as log:
        log.write('[%s] %s \n' %(strftime('%Y-%m-%d %H:%M:%S'), text))

def save_texts(texts, created_ats):
    # get string
    created_range = '%s - %s (%s)' %(created_ats[-1], created_ats[0], len(texts))
    texts.reverse()
    text = '\n'.join(texts)
    del texts[:]
    del created_ats[:]

    # write
    fname = os.path.join(destdir, '%s.txt' % created_range)
    if os.path.isfile(fname):
        logging('%s is alread exists' % fname)
    try:
        with open(fname, 'a') as f:
            f.write(created_range.encode('utf-8'))
            f.write('\n\n')
            f.write(text.encode('utf-8'))
    except Exception:
        logging('%s Write Exception' % fname)


if __name__=='__main__':
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tw.API(auth)

    fname = None
    texts = []
    created_ats = []

    dates = map(lambda x: '0'+str(x) if x < 10 else str(x), range(5, 11))
    daterange = ['2016-08-%s' % date for date in dates]

    for i in range(len(daterange)-1):
        j = 0
        logging('crawl started since %s, until %s' %(daterange[i], daterange[i+1]))
        cur = tw.Cursor(api.search, q=u'자살', since=daterange[i], until=daterange[i+1], lang='ko').items()
        logging(' --- SUCCESS')
        while True:
            try:
                tweet  = cur.next()
            except tw.TweepError:
                logging('Sleep')
                sleep(60*15)
                logging(' --- SUCCESS')
                continue
            except StopIteration:
                logging('Stop Iteration')
                if texts: save_texts(texts, created_ats)
                break
            except:
                logging('Exception')
                if texts: save_texts(texts, created_ats)
                break

            j += 1

            texts.append('[%s] %s' %(tweet.created_at, tweet.text))
            created_ats.append(tweet.created_at)

            if j >= 100:
                # reset
                j = 0
                if not texts: continue
                save_texts(texts, created_ats)

        logging('%s - %s is done' %(daterange[i], daterange[i+1]))

    logging('Stop Crawling')
