import feedparser
import requests
import re
import os
from datetime import datetime
from html import unescape

KEYWORDS_FAMILY = [
    'семейное право', 'семейный кодекс', 'брачный договор', 'расторжение брака',
    'развод', 'алименты', 'алимент', 'опека над', 'родительские права',
    'лишение родительских прав', 'имущество супругов', 'раздел имущества',
    'совместно нажитое', 'бракоразводный', 'сожительство', 'фактический брак',
    'материнский капитал', 'дети от разных браков', 'отцовство', 'материнство',
    'установление отцовства', 'порядок общения с ребенком', 'место жительства ребенка'
]

KEYWORDS_LABOR = [
    'трудовое право', 'трудовой кодекс', 'трудовой договор', 'увольнение по',
    'необоснованное увольнение', 'восстановление на работе', 'трудовая инспекция',
    'трудовая книжка', 'запись в трудовой', 'испытательный срок', 'оплачиваемый отпуск',
    'отпуск без сохранения', 'декретный отпуск', 'отпуск по уходу за ребенком',
    'переработка', 'сверхурочные', 'задержка зарплаты', 'зарплатная задолженность',
    'дисциплинарное взыскание', 'прогул', 'прогул без уважительной', 'штраф работодателя',
    'командировочные', 'больничный лист', 'листок нетрудоспособности', 'профзаболевание',
    'сокращение штата', 'сокращение численности', 'выплата при сокращении',
    'коллективный договор', 'профсоюз', 'забастовка', 'трудовой спор'
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
        print(f"SKIP: {title[:60]}")
        return
    
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
                print(f"SKIP: {title[:60]}")
    except Exception as e:
        print(f"ERROR {url}: {e}")

def generate_index():
    posts_html = []
    for fname in sorted(os.listdir(POSTS_DIR), reverse=True):
        if not fname.endswith('.md'):
            continue
        with open(os.path.join(POSTS_DIR, fname), 'r', encoding='utf-8') as f:
            content = f.read()
        
        title = 'Без названия'
        date = ''
        category = ''
        link = ''
        for line in content.split('\n'):
            if line.startswith('title:'):
                title = line[6:].strip().strip('"')
            elif line.startswith('date:'):
                date = line[5:].strip()[:10]
            elif line.startswith('categories:'):
                category = line[11:].strip()
            elif line.startswith('link:'):
                link = line[5:].strip()
        
        cat_badge = f'<span class="cat">{category}</span>' if category else ''
        source_link = f'<p><a href="{link}" target="_blank">Читать источник →</a></p>' if link else ''
        
        posts_html.append(f'''<div class="post">
<h2>{title}</h2>
<div class="meta">📅 {date} | 🏷️ {cat_badge}</div>
{source_link}
</div>''')
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Юридический дайджест</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #333; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
.post {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
.post h2 {{ margin-top: 0; font-size: 18px; color: #2c3e50; }}
.meta {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
.cat {{ background: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
a {{ color: #3498db; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.empty {{ text-align: center; color: #999; padding: 40px; }}
</style>
</head>
<body>
<h1>⚖️ Юридический дайджест</h1>
<p>Автоматическая подборка новостей по <strong>семейному</strong> и <strong>трудовому</strong> праву РФ.</p>
{''.join(posts_html) if posts_html else '<div class="empty">Пока записей нет. Бот собирает новости каждый день в 9:00, или <a href="https://github.com/IvanX888/legal-blog/actions">запусти его вручную</a>.</div>'}
</body>
</html>'''
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Generated index.html")

if __name__ == '__main__':
    for url, name in FEEDS:
        fetch_feed(url, name)
    generate_index()
    print("Done!")
