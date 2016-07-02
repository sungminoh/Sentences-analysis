# coding: utf-8

import tweepy as tw
import traceback

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
    
    i = 0
    j = 0
    for tweet in tw.Cursor(api.search, q=u'자살', since='2016-06-01', until='2016-06-30', lang='ko').items():
        j += 1

        texts.append(tweet.text)
        
        if j >= 10:
            # reset
            i += 1
            j = 0

            # get string
            if not texts: continue
            fname = './posts/%s_%s.txt' %(str(tweet.created_at), str(i))
            title = None
            for t in texts:
                title = t[0:50]
                if len(title) > 10: break
            text = '\n'.join(texts)
            del texts[:]
            
            # write
            try:
                with open(fname, 'w') as f:
                    f.write(title.encode('utf-8'))
                    f.write('\n')
                    f.write(text.encode('utf-8'))
            except Exception:
                print title
                print



 


