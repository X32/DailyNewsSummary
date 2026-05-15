# 每日新闻摘要系统

## 项目架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        定时调度层 (schedule.py)                       │
│              每2小时触发一次爬取 + 摘要的完整流程                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │                     │
          ┌─────────▼─────────┐  ┌───────▼───────────┐
          │   crawler.py      │  │  summarize.py     │
          │   (数据采集层)      │  │  (AI摘要层)        │
          │                   │  │                    │
          │  news.sina.com.cn │  │  1.按超链接爬取正文  │
          │  ├─ get_hots()    │  │  2.调用LLM生成摘要  │
          │  ├─ get_mils()    │  │  3.更新summary字段  │
          │  └─ get_news()    │  │                    │
          │                   │  │  .env 配置:         │
          │  tech.sina.com.cn │  │  ├─ LLM_API_KEY    │
          │  ├─ get_tech_     │  │  ├─ LLM_BASE_URL   │
          │  │  headlines()   │  │  └─ LLM_MODEL      │
          │  └─ get_tech_     │  │                    │
          │     feed()        │  │  支持: Qwen/DeepSeek│
          └────────┬──────────┘  └────────┬───────────┘
                   │                      │
                   │  写入                 │  读取 + 更新
                   ▼                      ▼
          ┌─────────────────────────────────────────┐
          │            MySQL (dailynews)             │
          │            news.py (ORM层)               │
          │                                         │
          │  News 表:                                │
          │  ┌──────────┬──────────┬──────────────┐  │
          │  │ id       │ headline │ hyperlink    │  │
          │  │ category │ content  │ summary      │  │
          │  │ createtime          │              │  │
          │  └──────────┴──────────┴──────────────┘  │
          │                                         │
          │  .env 配置:                               │
          │  ├─ DB_HOST / DB_PORT                    │
          │  ├─ DB_NAME / DB_USER                    │
          │  └─ DB_PASSWORD                          │
          └──────────────────┬──────────────────────┘
                             │
                             │ SQLModel 查询
                             ▼
          ┌─────────────────────────────────────────┐
          │        main.py (Web后端 / FastAPI)       │
          │                                         │
          │  路由:                                   │
          │  ├─ GET /              → 今日要闻        │
          │  ├─ GET /{category}    → 按分类查询      │
          │  └─ GET /{date}/{cat}  → 按日期+分类查询 │
          │                                         │
          │  分类: hot china world mil finance        │
          │        tech ent society                  │
          └──────────────────┬──────────────────────┘
                             │
                             │ Jinja2 渲染
                             ▼
          ┌─────────────────────────────────────────┐
          │     templates/news.html (前端展示层)      │
          │                                         │
          │  ┌───────────────────────────────────┐   │
          │  │  导航栏: 日期 + 8个分类链接          │   │
          │  ├───────────────────────────────────┤   │
          │  │  新闻列表 (循环渲染)                │   │
          │  │  ├─ 标题 + 查看原文链接             │   │
          │  │  └─ AI摘要内容                     │   │
          │  ├───────────────────────────────────┤   │
          │  │  底部: 历史日期导航                  │   │
          │  └───────────────────────────────────┘   │
          └─────────────────────────────────────────┘
```

## 数据流向

```
新浪新闻网页 → crawler.py(爬取) → MySQL(存储) → summarize.py(LLM摘要) → main.py(FastAPI路由) → news.html(浏览器展示)
```

## 各层职责

| 层级   | 文件                    | 职责                                                                    |
| ------ | ----------------------- | ----------------------------------------------------------------------- |
| 调度层 | `schedule.py`         | 定时触发爬取和摘要，每2小时运行一次                                     |
| 采集层 | `crawler.py`          | 爬取 `news.sina.com.cn`(7个分类) + `tech.sina.com.cn`(科技)，写入DB |
| AI层   | `summarize.py`        | 爬取新闻正文，调用LLM生成100字摘要，更新DB                              |
| ORM层  | `news.py`             | SQLModel模型定义 + DB连接 + 查询方法                                    |
| 后端层 | `main.py`             | FastAPI路由，按日期/分类查询，Jinja2渲染模板                            |
| 前端层 | `templates/news.html` | 展示新闻列表、分类导航、历史日期                                        |
| 配置层 | `.env`                | 数据库配置 + LLM模型配置(支持Qwen/DeepSeek切换)                         |

## 执行顺序

1. `python crawler.py` — 爬取新闻标题和链接，写入数据库（summary 字段为空）
2. `python summarize.py` — 读取未生成摘要的新闻，调用 LLM API 生成摘要并更新数据库
3. `python main.py` — 启动 FastAPI Web 服务，查询已摘要的新闻并展示

`schedule.py` 是把步骤1和2合并定时执行的：

```
schedule.py
  └── 每 2 小时触发：
      ├── crawler.py  (爬取)
      └── summarize.py (摘要)
```

## LLM 模型配置

在 `.env` 中配置 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 三个项，切换模型只需修改配置：

| 模型     | LLM_BASE_URL                                          | LLM_MODEL         |
| -------- | ----------------------------------------------------- | ----------------- |
| DeepSeek | `https://api.deepseek.com`                          | `deepseek-chat` |
| Qwen     | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus`     |

## 依赖

fastapi, uvicorn, sqlmodel, pymysql, beautifulsoup4, lxml, openai, python-dotenv, requests, jinja2
