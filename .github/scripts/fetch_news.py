import feedparser
import requests
import re
import os
from datetime import datetime
from html import unescape

# === НАСТРОЙКИ ===
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

# Расширенные источники
FEEDS = [
    ('https://www.garant.ru/news/rss/', 'ГАРАНТ'),
    ('https://rg.ru/xml/index.xml', 'Российская газета'),
    ('https://duma.gov.ru/news/rss/', 'Госдума'),
    ('https://www.kommersant.ru/rss/doc.xml', 'Коммерсантъ'),
    ('https://pravo.ru/rss/news/', 'Право.ру'),
    ('https://www.rbc.ru/rss/', 'РБК'),
    ('https://tass.ru/rss/v2.xml', 'ТАСС'),
    ('https://www.vedomosti.ru/rss/news', 'Ведомости'),
    ('https://www.interfax.ru/rss.asp', 'Интерфакс'),
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
        
        for entry in feed.entries[:8]:
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
        print(f"ERROR {source_name}: {e}")

def get_weather(lat, lon, city):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&timezone=auto"
        r = requests.get(url, timeout=10)
        data = r.json()
        temp = data['current']['temperature_2m']
        return f"{city} {temp}°C"
    except Exception:
        return f"{city} --°C"

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
        source = ''
        for line in content.split('\n'):
            if line.startswith('title:'):
                title = line[6:].strip().strip('"')
            elif line.startswith('date:'):
                date = line[5:].strip()[:10]
            elif line.startswith('categories:'):
                category = line[11:].strip()
            elif line.startswith('link:'):
                link = line[5:].strip()
            elif line.startswith('source:'):
                source = line[7:].strip()
        
        cat_class = 'cat-family' if 'семейное' in category else 'cat-labor'
        source_link = f'<a href="{link}" target="_blank" class="read-more">Читать источник →</a>' if link else ''
        
        posts_html.append(f'''<article class="post">
<h2>{title}</h2>
<div class="meta">
<span class="date">📅 {date}</span>
<span class="badge {cat_class}">{category}</span>
<span class="source">📰 {source}</span>
</div>
{source_link}
</article>''')
    
    weather_minsk = get_weather(53.9, 27.5667, 'Минск')
    weather_moscow = get_weather(55.7558, 37.6173, 'Москва')
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Юридический дайджест</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
.container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
header {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); border-radius: 16px; padding: 30px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }}
.header-top {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }}
h1 {{ font-size: 28px; color: #2c3e50; display: flex; align-items: center; gap: 10px; }}
.subtitle {{ color: #666; margin-top: 8px; font-size: 15px; }}
.weather {{ display: flex; gap: 15px; }}
.weather span {{ background: #e3f2fd; color: #1565c0; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 500; }}
nav {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; }}
nav a {{ color: #667eea; text-decoration: none; font-weight: 500; margin-right: 20px; }}
nav a:hover {{ text-decoration: underline; }}
.post {{ background: white; border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); transition: transform 0.2s; }}
.post:hover {{ transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,0.12); }}
.post h2 {{ font-size: 20px; color: #2c3e50; margin-bottom: 12px; line-height: 1.4; }}
.meta {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 15px; font-size: 13px; color: #666; }}
.badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
.cat-family {{ background: #fce4ec; color: #c2185b; }}
.cat-labor {{ background: #e8f5e9; color: #388e3c; }}
.read-more {{ display: inline-block; margin-top: 10px; color: #667eea; text-decoration: none; font-weight: 500; }}
.read-more:hover {{ text-decoration: underline; }}
.empty {{ background: white; border-radius: 16px; padding: 60px 20px; text-align: center; color: #999; }}
footer {{ text-align: center; padding: 30px; color: rgba(255,255,255,0.8); font-size: 14px; }}
footer a {{ color: white; font-weight: 600; }}
@media (max-width: 600px) {{
  .header-top {{ flex-direction: column; align-items: flex-start; }}
  .post h2 {{ font-size: 17px; }}
}}
</style>
</head>
<body>
<div class="container">
<header>
<div class="header-top">
<div>
<h1>⚖️ Юридический дайджест</h1>
<p class="subtitle">Подборка актуальных новостей по <strong>семейному</strong> и <strong>трудовому</strong> праву РФ</p>
</div>
<div class="weather">
<span>🌤️ {weather_minsk}</span>
<span>🌤️ {weather_moscow}</span>
</div>
</div>
<nav>
<a href="https://серко.рф" target="_blank">← На главный сайт серко.рф</a>
<a href="https://github.com/IvanX888/legal-blog" target="_blank">GitHub</a>
</nav>
</header>

{''.join(posts_html) if posts_html else '<div class="empty"><h3>Пока записей нет</h3><p>Бот собирает новости каждый день в 9:00. Вы можете <a href="https://github.com/IvanX888/legal-blog/actions">запустить его вручную</a> или добавить статью самостоятельно в папку _posts.</p></div>'}

<footer>
<p>© Юридический дайджест | <a href="https://серко.рф" target="_blank">серко.рф</a></p>
</footer>
</div>
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
