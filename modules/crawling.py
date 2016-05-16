from glob import glob
import os

def crawl():
    files = glob(os.path.dirname(os.path.abspath(__file__)) + '/../news_crawling/news_crawling/spiders/posts/*.txt')
    return files

if __name__=='__main__':
    print crawl()
