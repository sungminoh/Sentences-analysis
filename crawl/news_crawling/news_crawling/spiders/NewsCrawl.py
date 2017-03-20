# -*- coding: utf-8 -*-
import scrapy
import lxml.html
import sys
sys.path.append('../../..')


def remove_tags(text):
    return ''.join(lxml.html.fromstring(text).text_content())


class NewsCrawl(scrapy.Spider):
    # cur = connect_db().cursor()
    # topic_id = 0
    # source_id = 0
    i = 0
    name = "news"
    allowed_domains = ["chosun.com"]
    start_urls = [
        "http://search.chosun.com/search/news.search?query=%EC%9E%90%EC%82%B4&pageno="+str(x)+"&orderby=&naviarraystr=&kind=&cont1=&cont2=&cont5=&categoryname=&categoryd2=&c_scope=news&sdate=&edate=&premium=" for x in range(1, 51)
    ]

    def parse(self, response):
        for sel in response.xpath('//section[@class="result news"]/dl/dt'):
            url = sel.xpath('a/@href').extract()[0]
            yield scrapy.Request(url, callback=self.parse_content)

    def parse_content(self, response):
        title = response.xpath('//h1[@id="news_title_text_id"]/text()')[0].extract().strip()
        url = response.url
        timestamp = response.xpath('//p[@id="date_text"]/text()')[0].extract().strip().split(' : ')[-1]
        content = ''
        for sel in response.xpath('//div[@class="par"]'):
            content += remove_tags(sel.extract().replace('<BR>', '\n').replace('<br>', '\n'))

        content.strip()
        if not content:
            return

        f = open('./posts/%s_%s.txt' % (timestamp, self.i), 'w')
        self.i += 1
        f.write('%s\n%s\n%s' % (title, url, content))
        f.close()
