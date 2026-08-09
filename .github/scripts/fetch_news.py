import feedparser
import requests
import re
import os
from datetime import datetime
from html import unescape

# === НАСТРОЙКИ ===
KEYWORDS_FAMILY = [
    'семейное право', 'развод', 'алименты', 'брак', 'опека', 'родительские права',
    'супруги', 'имущество супругов', 'семейный кодекс', 'дети', 'ребенок', 'материнство',
    'отцовство', 'лишение родительских прав', 'брачный договор', 'сожительство'
]

KEYWORDS_LABOR = [
    'трудовое право', 'увольнение', 'отпуск', 'зарплата', 'трудовой договор',
    'трудовая инспекция', 'декрет', 'прогул', 'дисциплинарка', 'тк рф', 'кзот',
    'необоснованное увольнение', 'восстановление на работе', 'переработка', 'штраф',
    'трудовая книжка', 'испытательный срок', 'командировка', 'больничный'
]

FEEDS = [
    ('https://www.garant.ru/news/rss/', 'ГАРАНТ'),
    ('https://rg.ru/xml/index.xml', 'Российская газета'),
    ('https://duma.gov.ru/news/rss/', 'Госдума'),
    ('https://www.kommersant.ru/rss/doc.xml', 'Коммерсантъ'),
]

POSTS_DIR = '_posts'
os.makedirs(POSTS_DIR, exist_ok=True)

def normalize(text):
    return unescape(text).lower()

def has_keywords(text, keywords):
    t = normalize(text)
    return any(kw.lower() in t for kw in keywords)

def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)[:50]

def already_exists(link):
    for fname in os.listdir(POSTS_DIR):
        if fname.endswith('.md'):
            with open(os.path.join(POSTS_DIR, fname), 'r', encoding='utf-8') as f:
                if link in f.read():
                    return True
    return False

def create_post(title, link, summary, source, category):
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H-%M-%S')
    slug = slugify(title) or 'news'
    filename = f"{POSTS_DIR}/{date}-{time}-{slug}.md"
    
    if already_exists(link):
        print(f"SKIP (already exists): {title[:60]}")
        return
    
    # Исправление: экранируем кавычки ДО f-строки
    title_escaped = title.replace('"', '\\"')
    now_time = datetime.now().strftime('%H:%M:%S')
    
    content = f"""---
layout: post
title: "{title_escaped}"
date: {date} {now_time} +0300
categories: {category}
source: {source}
link: {link}
---

**Источник:** [{source}]({link})

{summary}

---
*Автоматически добавлено агентом*
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"CREATED: {filename}")

def fetch_feed(url, source_name):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; LegalBot/1.0)'}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        
        for entry in feed.entries[:10]:
            title = entry.get('title', 'Без названия')
            link = entry.get('link', '')
            summary = entry.get('summary', entry.get('description', ''))
            text = f"{title} {summary}"
            
            if has_keywords(text, KEYWORDS_FAMILY):
                create_post(title, link, summary, source_name, 'семейное-право')
            elif has_keywords(text, KEYWORDS_LABOR):
                create_post(title, link, summary, source_name, 'трудовое-право')
            else:
                print(f"SKIP (no keywords): {title[:60]}")
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")

if __name__ == '__main__':
    for url, name in FEEDS:
        fetch_feed(url, name)
    print("Done!")
