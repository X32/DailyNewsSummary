# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daily news aggregator that crawls Sina News, summarizes articles via DeepSeek LLM, and displays them through a FastAPI web app. Built as a chapter04 demo for an AI agent course.

## Running the Application

```bash
# Start the web server
python main.py

# Run the crawler manually
python crawler.py

# Run summarization on today's unsummarized news
python summarize.py

# Start the scheduled crawler + summarizer (runs every 2 hours at :30)
python schedule.py
```

Requires a `.env` file with `DeepSeek_API_Key` for LLM summarization.

Requires MySQL running at `127.0.0.1:3306` with database `dailynews`. Schema is in `dailynews.sql`.

## Architecture

**Data flow:** Sina News HTML → crawler.py (BeautifulSoup scraping) → MySQL (SQLModel) → summarize.py (DeepSeek API) → main.py (FastAPI/Jinja2) → browser

**Key modules:**

- `news.py` — `News` SQLModel table definition, database engine (MySQL+pymysql), and `get_news_by_dc()` query helper. All other modules import `engine` and `News` from here.
- `crawler.py` — Scrapes `news.sina.com.cn` for categories: hot, mil, china, world, finance, ent. Deduplicates by hyperlink before inserting.
- `summarize.py` — Fetches article body from hyperlink, sends to DeepSeek (`deepseek-chat` via OpenAI-compatible API) for ~100-char summary, updates DB rows.
- `main.py` — FastAPI app with routes: `/` (today's hot news), `/{category}` (today by category), `/{date}/{category}` (historical). Renders `templates/news.html`.
- `schedule.py` — Polling loop (60s interval) that triggers crawl + summarize every 2 hours at minute 30.
- `bs_demo.py` — Standalone BeautifulSoup demo script, not part of the main pipeline.

## Dependencies

fastapi, uvicorn, sqlmodel, pymysql, beautifulsoup4, lxml, openai, python-dotenv, requests, jinja2
