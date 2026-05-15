from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn, time
from sqlmodel import Session, select, text
from dotenv import load_dotenv
from news import engine, News, get_news_by_dc

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get('/')
def index(request: Request):
    # 先通过分组查询获取到所有的日期数据（截取createtime前10个字符）
    sql = text("select DISTINCT SUBSTRING(createtime, 1, 10) as mydate from news")
    with Session(engine) as session:
        result = session.execute(sql)
    date_list = result.mappings().all()

    today = time.strftime("%Y-%m-%d")
    news_list = get_news_by_dc(date=today)
    return templates.TemplateResponse(request=request, name="news.html", context={"news_list": news_list, "date_list": date_list, "today": today})

@app.get('/{category}')
def query_news(request: Request, category: str):
    today = time.strftime("%Y-%m-%d")
    news_list = get_news_by_dc(date=today, category=category)
    return templates.TemplateResponse(request=request, name="news.html",
                context={"news_list": news_list, "today": today})

@app.get('/{date}/{category}')
def query_news_dc(request: Request, date: str, category: str):
    # 先通过分组查询获取到所有的日期数据（截取createtime前10个字符）
    sql = text("select DISTINCT SUBSTRING(createtime, 1, 10) as mydate from news")
    with Session(engine) as session:
        result = session.execute(sql)
    date_list = result.mappings().all()

    today = date    # 将today变量更新为date参数的值，而非获取当天的日期
    news_list = get_news_by_dc(date=date, category=category)
    return templates.TemplateResponse(request=request, name="news.html", context={"news_list": news_list, "date_list": date_list, "today": today})

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)