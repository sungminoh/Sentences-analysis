# coding: utf-8

import tweepy as tw
import traceback
from time import strftime, sleep
import os

access_token = '1507884330-zKrVVS279t8dolO9y2cGw8d0HCVHDyGz03kSom7'
access_token_secret = 'AZSbHnLftFQ7ks0CkJxHQwm0d9o6fEswKpJdHAxxqVDSH'
consumer_key = '2NSSqRIlmfH7kjWVScPUbxUlh'
consumer_secret = 'Tr9QkCL7AdbT886X7gHMa6vjnjAYklroi9uOkkdWKuY6jX8XjO'
flogname = './crawl.log'
destdir = './posts_07_'

def save_texts(texts, created_ats):
    # get string
    created_range = '%s - %s (%s)' %(created_ats[-1], created_ats[0], len(texts))
    texts.reverse()
    text = '\n'.join(texts)
    del texts[:]
    del created_ats[:]
    
    # write
    fname = os.path.join(destdir, '%s.txt' % created_range)
    try:
        with open(fname, 'a') as f:
            f.write(created_range.encode('utf-8'))
            f.write('\n\n')
            f.write(text.encode('utf-8'))
    except Exception:
        with open(flogname, 'a') as log:
            log.write('[%s] %s Write Exception\n' %(strftime('%Y-%m-%d %H:%M:%S'), fname))


if __name__=='__main__':
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tw.API(auth)
    
    fname = None
    texts = []
    created_ats = []

    dates = map(lambda x: '0'+str(x) if x < 10 else str(x), range(1, 14))
    daterange = ['2016-07-%s' % date for date in dates]

    for i in range(len(daterange)-1):
        j = 0
        print daterange[i]
        with open(flogname, 'a') as log:
            log.write('[%s] crawl started since %s, until %s' %(strftime('%Y-%m-%d %H:%M:%S'), daterange[i], daterange[i+1]))
        cur = tw.Cursor(api.search, q=u'자살', since=daterange[i], until=daterange[i+1], lang='ko').items()
        with open(flogname, 'a') as log:
            log.write(' --- SUCCESS\n')
        while True:
            try:
                tweet  = cur.next()
            except tw.TweepError:
                with open(flogname, 'a') as log:
                    log.write('[%s] Sleep' %(strftime('%Y-%m-%d %H:%M:%S')))
                sleep(60*15)
                with open(flogname, 'a') as log:
                    log.write(' --- SUCCESS\n')
                continue
            except StopIteration:
                with open(flogname, 'a') as log:
                    log.write('[%s] Stop Iteration\n' %(strftime('%Y-%m-%d %H:%M:%S')))
                if texts: save_texts(texts, created_ats)
                break
            except:
                with open(flogname, 'a') as log:
                    log.write('[%s] Exception\n' %(strftime('%Y-%m-%d %H:%M:%S')))
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
        
        with open(flogname, 'a') as log:
            log.write('[%s] %s - %s is done\n' %(strftime('%Y-%m-%d %H:%M:%S'), daterange[i], daterange[i+1]))

    with open(flogname, 'a') as log:
        log.write('[%s] Stop Crawling\n' %(strftime('%Y-%m-%d %H:%M:%S')))
    log.close()
