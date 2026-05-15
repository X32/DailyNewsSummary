import time
from crawler import get_hots, get_mils, get_news, get_tech_news
from summarize import get_and_update
from datetime import datetime

if __name__ == '__main__':
    now = datetime.now()
    while True:
        # 每2个小时的第30分钟时执行一次
        if now.hour % 2 == 0 and now.minute == 30:
                get_hots()
                get_mils()
                get_news()
                get_tech_news()
                get_and_update()
                print("更新新闻完成", {now})
        else:
            print("定时任务正在运行中，请勿结束。")

        time.sleep(60)   # 每60秒钟运行一次