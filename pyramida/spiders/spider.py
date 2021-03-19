import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import PyramidaItem
from itemloaders.processors import TakeFirst
import json
import requests

pattern = r'(\xa0)?'

url = "https://www.modrapyramida.cz/api/articles/getbyfilterforkb"

payload = "{{\"dateFrom\":null,\"dateTo\":null,\"selectedCategories\":[\"TiskoveZpravy\"],\"articlesNumber\":{},\"limit\":1}}"
headers = {
    'authority': 'www.modrapyramida.cz',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'content-type': 'application/json',
    'accept': '*/*',
    'origin': 'https://www.modrapyramida.cz',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.modrapyramida.cz/o-modre/pro-media',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': 'CMSPreferredCulture=cs-CZ; CurrentContact=76c3acf9-6394-4c8d-929e-e6f71a265e52; _fbp=fb.1.1614851266937.1977263171; ssupp.vid=viNoAHYbevwSx; cookielaw=1; CMSCsrfCookie=VWISOx2fgg/UsJ6Y7Y4vCGqb5zoR25sQcLfhYwuT; ASP.NET_SessionId=oatcocmdizphkwm0nfnqlv31; CMSLandingPageLoaded=true; wt3_sid=%3B678118889516837; _gid=GA1.2.536761543.1616145145; wt_cdbeid=f62d96fba453d8c87a2736d5333b953f; ssupp.visits=2; wt_geid=68934a3e9455fa72420237eb; wt3_eid=%3B678118889516837%7C2161485126613563117%232161614542976360364; wt_rla=678118889516837%2C5%2C1616145144547; _ga=GA1.1.817541950.1614851266; _ga_Z68E6LLB47=GS1.1.1616145144.2.1.1616145430.0'
}


class PyramidaSpider(scrapy.Spider):
    name = 'pyramida'
    start_urls = ['https://www.modrapyramida.cz/o-modre/pro-media']
    article_index = 0

    def parse(self, response):
        data = requests.request("POST", url, headers=headers, data=payload.format(self.article_index))
        data = json.loads(data.text)
        date = data['payload']['articles'][0]['date'].split('T')[0]
        link = data['payload']['articles'][0]['url']
        yield response.follow(link, self.parse_post,cb_kwargs=dict(date=date))

        if self.article_index < data['payload']['totalCount']:
            self.article_index += 1
            yield response.follow(response.url, self.parse, dont_filter=True)

    def parse_post(self, response, date):

        title = response.xpath('//h1/text()').get()
        content = response.xpath('//div[@class="text-block__content ignore-wysiwyg"]//text()').getall()
        content = [p.strip() for p in content if p.strip()]
        content = re.sub(pattern, "",' '.join(content))

        item = ItemLoader(item=PyramidaItem(), response=response)
        item.default_output_processor = TakeFirst()

        item.add_value('title', title)
        item.add_value('link', response.url)
        item.add_value('content', content)
        item.add_value('date', date)

        yield item.load_item()
