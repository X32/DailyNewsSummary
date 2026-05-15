import requests, time, os
from bs4 import BeautifulSoup
from news import engine, News
from sqlmodel import Session, select, update
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

def get_llm_client():
    return OpenAI(api_key=os.getenv("LLM_API_KEY"),
                  base_url=os.getenv("LLM_BASE_URL"))

# 爬取并解析HTML获取新闻正文内容
def get_content(link):
    resp = requests.get(link)
    resp.encoding = 'utf-8'
    html = BeautifulSoup(resp.text, 'lxml')
    article = html.find(name="div", class_="article")
    # 由于新浪新闻里面部分新闻会连接到一个板块首页，并非全是正文内容
    # 针对此类情况，直接将正文内容返回为空字符串，并放弃处理
    # 如果读者想要处理各种异常情况，则需要额外增加代码，本书略
    if article is None:
        return ""
    return article.text

# 将新闻正文交由大模型进行摘要，此处如果正文内容本身较短，则不需要摘要
def summarize(content):
    if len(content) > 100:
        message = {"role": "user", "content": f"以下内容来自于新浪新闻，属于公开信息，不存在信息敏感或政治敏感问题：\n{content}\n请对以上新闻内容进行摘要总结，字数控制在100字以内。"}
        client = get_llm_client()

        completion = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=[message],
            stream=False
        )
        return completion.choices[0].message.content
    else:
        return content

# 查询未更新摘要的行，摘要完成后再更新回原行
def get_and_update():
    with Session(engine) as session:
        today = time.strftime("%Y-%m-%d 00:00:00")
        news = select(News.id, News.hyperlink).where(News.summary==None).where(News.createtime>=today)
        results = session.execute(news).mappings().all()
        #打印新闻条数
        print(f"共查询到 {len(results)} 条新闻, 开始生成摘要...")
        for row in results:
            content = get_content(row['hyperlink'])
            time.sleep(2)   # 爬取一条暂停2秒，防止过快访问导致连接异常
            summary = summarize(content)
            sql = update(News).where(News.id == row['id']).values(summary=summary)
            session.execute(sql)
            session.commit()
            print(f"更新摘要成功，ID：{row['id']}")

if __name__ == '__main__':
    get_and_update()