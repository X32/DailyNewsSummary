import requests
from bs4 import BeautifulSoup

url = "https://news.sina.com.cn/"
resp = requests.get(url)
resp.encoding = 'utf-8'

# 此处使用lxml解析器，将响应代码转换为BS文档对象
# lxml解析器有解析HTML和XML的功能，而且速度快，容错能力强
# BS的解析引擎一共有4种，参考：https://www.cnblogs.com/feng0815/p/16694808.html
html = BeautifulSoup(resp.text, 'lxml')

# 获取页面中的DIV，其id属性为syncad_1，class属性为ct_t_01
# 具体页面的元素类别和对应的属性需要通过查看源代码获取到
# daily_hots = html.find(name="div", id="syncad_1", class_="ct_t_01")
#
# # BeautifulSoup中主要使用find和find_all查找元素
# # find表示通过指定属性查找某一个元素，find_all表示查找所有元素
# for news in daily_hots.find_all("h1", attrs={"data-client": "headline"}):
#     links = news.find_all("a", class_="linkNewsTopBold")
#     for link in links:
#         # 获取对应元素的href属性或文本内容
#         hyperlink = link.get("href")
#         headline = link.text
#         print(hyperlink, headline)



china_news = html.find('ul', class_='list_14_noBg', id='blk_gnxw_011', attrs={"data-client": "p_china"})
for news in china_news.find_all("li"):
    link = news.find("a")
    hyperlink = link.get("href")
    headline = link.text
    print(hyperlink, headline)