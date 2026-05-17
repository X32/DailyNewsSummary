import time
from crawler import get_hots, get_mils, get_news, get_tech_news
from summarize import get_and_update
from datetime import datetime


def crawl_all_news():
    get_hots()                                   # 今日要闻 (hot)
    get_mils()                                   # 军事新闻 (mil)
    get_news("blk_gnxw_011", "p_china")          # 国内新闻 (china)
    get_news("blk_gjxw_011", "p_world")          # 国际新闻 (world)
    get_news("blk_cjkjqcfc_011", "p_finance")    # 财经新闻 (finance)
    get_news("blk_lctycp_011", "p_ent")          # 娱乐新闻 (ent)
    get_news("blk_sh_011", "p_society")          # 社会新闻 (society)
    get_tech_news()                              # 科技新闻 (tech)


if __name__ == '__main__':
    while True:
        now = datetime.now()
        # 每2个小时的第30分钟时执行一次
        if now.hour % 2 == 0 and now.minute == 30:
            crawl_all_news()
            get_and_update()
            print("更新新闻完成", now)
        else:
            print("定时任务正在运行中，请勿结束。")

        time.sleep(60)   # 每60秒钟运行一次
