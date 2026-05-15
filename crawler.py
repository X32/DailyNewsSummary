import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, select
from datetime import datetime
from news import engine, News

url = "https://news.sina.com.cn/"
resp = requests.get(url)
resp.encoding = 'utf-8'
html = BeautifulSoup(resp.text, 'lxml')

# 获取今日要闻的标题与超链接
def get_hots():
    daily_hots = html.find(name="div", id="syncad_1", class_="ct_t_01")
    for hots in daily_hots.find_all("h1", attrs={"data-client": "headline"}):
        links = hots.find_all("a", class_="linkNewsTopBold")
        for link in links:
            hyperlink = link.get("href")
            headline = link.text
            category = "hot"
            news = News(category=category, headline=headline, hyperlink=hyperlink, createtime=datetime.now())
            insert_news(news)

# 获取军事新闻标题与超链接
def get_mils():
    mil_news = html.find(name="div", id="blk_08_cont01", attrs={"data-sudaclick":"mil_1"})
    for line in mil_news.find_all("li"):
        link = line.find("a")
        hyperlink = link.get("href")
        headline = link.text
        category = "mil"
        news = News(category=category, headline=headline, hyperlink=hyperlink, createtime=datetime.now())
        insert_news(news)

# 获取国内国际科技娱乐军事等类别新闻
def get_news(id, type):
    attrs = {"class": "list_14_noBg"}
    if type:
        attrs["data-client"] = type
    daily_news = html.find(name="ul", id=id, **attrs)
    if daily_news is None:
        print(f"未找到板块: id={id}, type={type}")
        return
    for line in daily_news.find_all("li"):
        link = line.find("a")
        if link is None:
            continue
        hyperlink = link.get("href")
        headline = link.text
        category = type[2:] if type else id
        news = News(category=category, headline=headline, hyperlink=hyperlink, createtime=datetime.now())
        insert_news(news)

# 新增数据到数据库中
def insert_news(news):
    print(news)
    with Session(engine) as session:
        hyperlink = news.hyperlink
        query = select(News.id).where(News.hyperlink == hyperlink)
        result = session.exec(query).all()
        if len(result) > 0:
            print(f"数据{result}已经存在，不需要更新")
        else:
            session.add(news)
            session.commit()

# 请求并解析 tech.sina.com.cn 页面
def _fetch_tech_html():
    resp = requests.get("https://tech.sina.com.cn/")
    resp.encoding = 'utf-8'
    return BeautifulSoup(resp.text, 'lxml')

# 爬取科技频道顶部要闻列表
def get_tech_headlines(html):
    tech_news_div = html.find(name="div", class_="tech-news")
    if tech_news_div is None:
        print("未找到科技要闻板块")
        return
    ul = tech_news_div.find("ul")
    if ul is None:
        print("未找到科技要闻列表")
        return
    for li in ul.find_all("li", attrs={"data-sudaclick": lambda v: v and v.startswith("yaowenlist")}):
        link = li.find("a")
        if link is None:
            continue
        hyperlink = link.get("href")
        headline = link.text.strip()
        if not headline or not hyperlink:
            continue
        news = News(category="tech", headline=headline, hyperlink=hyperlink, createtime=datetime.now())
        insert_news(news)

# 爬取科技频道卡片式新闻流
def get_tech_feed(html):
    cardlist = html.find(name="div", id="j_cardlist")
    if cardlist is None:
        print("未找到科技新闻卡片列表")
        return
    for h3 in cardlist.find_all("h3", class_="ty-card-tt"):
        link = h3.find("a")
        if link is None:
            continue
        hyperlink = link.get("href")
        headline = link.text.strip()
        if not headline or not hyperlink:
            continue
        news = News(category="tech", headline=headline, hyperlink=hyperlink, createtime=datetime.now())
        insert_news(news)

# 爬取科技频道全部新闻（入口函数）
def get_tech_news():
    try:
        html = _fetch_tech_html()
        get_tech_headlines(html)
        get_tech_feed(html)
    except requests.RequestException as e:
        print(f"获取科技新闻页面失败: {e}")

if __name__ == '__main__':
    # get_hots()                                   # 今日要闻 (hot)
    # get_mils()                                   # 军事新闻 (mil)
    # get_news("blk_gnxw_011", "p_china")          # 国内新闻 (china)
    # get_news("blk_gjxw_011", "p_world")          # 国际新闻 (world)
    # get_news("blk_cjkjqcfc_011", "p_finance")    # 财经新闻 (finance)
    # get_news("blk_lctycp_011", "p_ent")          # 娱乐新闻 (ent)
    # get_news("blk_kjxwsjxjbjb_011", "p_tech")   # 科技新闻 (tech)
    # get_news("blk_sh_011", "p_society")          # 社会新闻 (society)
    get_tech_news()                                 # 科技频道新闻 (tech)