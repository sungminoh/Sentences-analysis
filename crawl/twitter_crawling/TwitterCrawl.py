# coding: utf-8

import tweepy as tw
import traceback
from time import strftime, sleep

access_token = '1507884330-zKrVVS279t8dolO9y2cGw8d0HCVHDyGz03kSom7'
access_token_secret = 'AZSbHnLftFQ7ks0CkJxHQwm0d9o6fEswKpJdHAxxqVDSH'
consumer_key = '2NSSqRIlmfH7kjWVScPUbxUlh'
consumer_secret = 'Tr9QkCL7AdbT886X7gHMa6vjnjAYklroi9uOkkdWKuY6jX8XjO'


if __name__=='__main__':
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tw.API(auth)
    
    fname = None
    texts = []
    created_ats = []

    flogname = './crawl.log'
    # daterange = ['2016-06-01', '2016-06-06', '2016-06-11', '2016-06-16', '2016-06-21', '2016-06-26', '2016-07-01']
    daterange = ['2016-06-01', '2016-06-06', '2016-06-11', '2016-06-16', '2016-06-21', '2016-06-24 16:52:01']

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
                break
            except:
                with open(flogname, 'a') as log:
                    log.write('[%s] Exception\n' %(strftime('%Y-%m-%d %H:%M:%S')))
                break

            j += 1

            texts.append('[%s] %s' %(tweet.created_at, tweet.text))
            created_ats.append(tweet.created_at)
            
            if j >= 100:
                # reset
                j = 0

                # get string
                if not texts: continue
                created_range = '%s - %s (%s)' %(created_ats[0], created_ats[-1], len(texts))
                text = '\n'.join(texts)
                del texts[:]
                del created_ats[:]
                
                # write
                fname = './posts/%s.txt' %(created_range)
                try:
                    with open(fname, 'a') as f:
                        f.write(created_range.encode('utf-8'))
                        f.write('\n\n')
                        f.write(text.encode('utf-8'))
                except Exception:
                    with open(flogname, 'a') as log:
                        log.write('[%s] %s Write Exception\n' %(strftime('%Y-%m-%d %H:%M:%S'), fname))
        
        with open(flogname, 'a') as log:
            log.write('[%s] %s - %s is done\n' %(strftime('%Y-%m-%d %H:%M:%S'), daterange[i], daterange[i+1]))

    with open(flogname, 'a') as log:
        log.write('[%s] Stop Crawling\n' %(strftime('%Y-%m-%d %H:%M:%S')))
    log.close()
