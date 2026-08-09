import feedparser
import requests
import re
import os
from datetime import datetime
from html import unescape

# === РАСШИРЕННЫЕ КЛЮЧЕВЫЕ СЛОВА ===
KEYWORDS_FAMILY = [
    'семейное право', 'семейный кодекс', 'брачный договор', 'расторжение брака',
    'развод', 'алименты', 'алимент', 'опека', 'родительские права',
    'лишение родительских прав', 'имущество супругов', 'раздел имущества',
    'бракоразводный', 'сожительство', 'фактический брак',
    'материнский капитал', 'отцовство', 'материнство',
    'установление отцовства', 'порядок общения с ребенком', 'место жительства ребенка',
    'суррогатное материнство', 'усыновление', 'удочерение', 'брачный контракт',
    'супружеская', 'супруг', 'супруга', 'дети', 'ребенок', 'несовершеннолетний',
    'патронаж', 'попечительство', 'семейный конфликт', 'домашнее насилие',
    'заявление на развод', 'развод в одностороннем', 'расторгнуть брак'
]

KEYWORDS_LABOR = [
    'трудовое право', 'трудовой кодекс', 'трудовой договор', 'увольнение',
    'необоснованное увольнение', 'восстановление на работе', 'трудовая инспекция',
    'трудовая книжка', 'испытательный срок', 'отпуск', 'декрет',
    'переработка', 'сверхурочные', 'задержка зарплаты', 'зарплатная задолженность',
    'дисциплинарное взыскание', 'прогул', 'штраф работодателя',
    'командировочные', 'больничный', 'профзаболевание',
    'сокращение штата', 'сокращение численности', 'выплата при сокращении',
    'коллективный договор', 'профсоюз', 'забастовка', 'трудовой спор',
    'выплаты при ликвидации', 'охрана труда', 'незаконное увольнение',
    'работник', 'работодатель', 'зарплата', 'заработная плата', 'труд',
    'кадровый', 'кадры', 'трудовые отношения', 'трудовая дисциплина',
    'восстановление на работе', 'вынужденный прогул', 'компенсация при увольнении'
]

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
    ('https://iz.ru/xml/rss/all.xml', 'Известия'),
    ('https://ria.ru/export/rss2/archive/index.xml', 'РИА Новости'),
    ('https://lenta.ru/rss/news', 'Лента.ру'),
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

def truncate(text, length=300):
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'

def create_post(title, link, summary, source, category, is_fallback=False):
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H-%M-%S')
    slug = slugify(title) or 'news'
    filename = f"{POSTS_DIR}/{date}-{time}-{slug}.md"
    
    if already_exists(link):
        print(f"  SKIP (exists): {title[:60]}")
        return False
    
    title_escaped = title.replace('"', '\\"')
    now_time = datetime.now().strftime('%H:%M:%S')
    short_summary = truncate(summary, 350)
    
    fallback_note = '\n\n> 💡 Эта новость добавлена как общая (не по ключевым словам)' if is_fallback else ''
    
    content = f"""---
layout: post
title: "{title_escaped}"
date: {date} {now_time} +0300
categories: {category}
source: {source}
link: {link}
---

**Источник:** [{source}]({link})

{short_summary}{fallback_note}
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  CREATED: {category} | {title[:60]}")
    return True

def fetch_feed(url, source_name):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        print(f"\n📡 {source_name}...")
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        
        if not feed.entries:
            print(f"  ⚠️  Нет записей в RSS")
            return
        
        print(f"  Всего записей в RSS: {len(feed.entries)}")
        
        found = 0
        fallback_count = 0
        
        for i, entry in enumerate(feed.entries[:20]):
            title = entry.get('title', 'Без названия')
            link = entry.get('link', '')
            summary = entry.get('summary', entry.get('description', ''))
            text = f"{title} {summary}"
            
            if has_keywords(text, KEYWORDS_FAMILY):
                if create_post(title, link, summary, source_name, 'семейное-право'):
                    found += 1
            elif has_keywords(text, KEYWORDS_LABOR):
                if create_post(title, link, summary, source_name, 'трудовое-право'):
                    found += 1
            else:
                # Fallback: берем первые 2 новости без фильтра
                if fallback_count < 2 and i < 5:
                    if create_post(title, link, summary, source_name, 'общие-новости', is_fallback=True):
                        fallback_count += 1
        
        print(f"  ✅ Найдено по теме: {found}, добавлено общих: {fallback_count}")
        
    except Exception as e:
        print(f"  ❌ ОШИБКА: {e}")

def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=55.7558&longitude=37.6173&current=temperature_2m,weather_code&timezone=Europe/Moscow"
        r = requests.get(url, timeout=10)
        data = r.json()
        temp = data['current']['temperature_2m']
        return f"Москва {temp}°C"
    except Exception:
        return "Москва --°C"

def generate_index():
    posts = []
    dates = set()
    
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
        summary = ''
        
        lines = content.split('\n')
        in_frontmatter = False
        frontmatter_done = False
        
        for line in lines:
            if line == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    frontmatter_done = True
                    in_frontmatter = False
                continue
            
            if not frontmatter_done:
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
            else:
                if line.startswith('**Источник:**'):
                    continue
                if line.startswith('> 💡'):
                    continue
                if line.strip() and not line.startswith('---'):
                    summary += line + ' '
        
        if date:
            dates.add(date)
        
        if 'семейное' in category:
            cat_class = 'cat-family'
        elif 'трудовое' in category:
            cat_class = 'cat-labor'
        else:
            cat_class = 'cat-general'
        
        short_text = truncate(summary.strip(), 300)
        
        posts.append({
            'title': title,
            'date': date,
            'category': category,
            'source': source,
            'link': link,
            'cat_class': cat_class,
            'summary': short_text
        })
    
    posts_html = []
    for post in posts:
        source_link = f'<a href="{post["link"]}" target="_blank" rel="noopener" class="read-more">Читать полностью →</a>' if post['link'] else ''
        posts_html.append(f'''<article class="post">
<h2>{post["title"]}</h2>
<div class="meta">
<span class="date">📅 {post["date"]}</span>
<span class="badge {post["cat_class"]}">{post["category"]}</span>
<span class="source">📰 {post["source"]}</span>
</div>
<p class="excerpt">{post["summary"]}</p>
{source_link}
</article>''')
    
    calendar_html = ''
    for d in sorted(dates, reverse=True)[:15]:
        calendar_html += f'<a href="#date-{d}" class="cal-date">{d}</a>'
    
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    weather = get_weather()
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Юридический дайджест — семейное и трудовое право РФ</title>
<meta name="description" content="Актуальные новости по семейному и трудовому праву Российской Федерации. Алименты, развод, трудовые споры, увольнение, декрет.">
<meta name="keywords" content="семейное право, трудовое право, алименты, развод, увольнение, трудовой кодекс, юрист, юридические новости, РФ">
<meta property="og:title" content="Юридический дайджест">
<meta property="og:description" content="Актуальные новости по семейному и трудовому праву РФ">
<meta property="og:type" content="website">
<meta property="og:url" content="https://серко.рф/legal-blog/">
<meta name="robots" content="index, follow">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; color: #333; }}
.container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
header {{ background: linear-gradient(135deg, #e94560 0%, #ff6b6b 50%, #c44569 100%); border-radius: 20px; padding: 35px; margin-bottom: 25px; box-shadow: 0 10px 40px rgba(233, 69, 96, 0.3); position: relative; overflow: hidden; }}
header::before {{ content: "⚖️"; position: absolute; right: 30px; top: 50%; transform: translateY(-50%); font-size: 80px; opacity: 0.15; }}
h1 {{ font-size: 32px; color: #fff; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
.subtitle {{ color: rgba(255,255,255,0.9); font-size: 16px; margin-bottom: 20px; }}
.header-info {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2); }}
.weather {{ background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); color: #fff; padding: 10px 20px; border-radius: 25px; font-size: 14px; font-weight: 600; }}
.time {{ color: rgba(255,255,255,0.8); font-size: 14px; }}
nav {{ margin-top: 15px; }}
nav a {{ color: #fff; text-decoration: none; font-weight: 600; margin-right: 25px; opacity: 0.9; transition: opacity 0.2s; }}
nav a:hover {{ opacity: 1; text-decoration: underline; }}
.calendar {{ background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; margin-bottom: 25px; }}
.calendar h3 {{ color: #fff; font-size: 16px; margin-bottom: 12px; }}
.cal-date {{ display: inline-block; background: rgba(255,255,255,0.15); color: #fff; padding: 6px 14px; border-radius: 20px; font-size: 13px; margin: 4px; text-decoration: none; transition: all 0.2s; }}
.cal-date:hover {{ background: #e94560; transform: scale(1.05); }}
.post {{ background: #fff; border-radius: 20px; padding: 30px; margin-bottom: 25px; box-shadow: 0 8px 30px rgba(0,0,0,0.15); transition: all 0.3s; border-left: 5px solid transparent; }}
.post:hover {{ transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.2); }}
.post:nth-child(3n+1) {{ border-left-color: #e94560; }}
.post:nth-child(3n+2) {{ border-left-color: #533483; }}
.post:nth-child(3n+3) {{ border-left-color: #0f3460; }}
.post h2 {{ font-size: 22px; color: #1a1a2e; margin-bottom: 15px; line-height: 1.4; }}
.meta {{ display: flex; gap: 15px; flex-wrap: wrap; align-items: center; margin-bottom: 15px; font-size: 14px; color: #666; }}
.badge {{ padding: 5px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
.cat-family {{ background: #fce4ec; color: #c2185b; }}
.cat-labor {{ background: #e8f5e9; color: #2e7d32; }}
.cat-general {{ background: #fff3e0; color: #e65100; }}
.excerpt {{ color: #555; line-height: 1.7; font-size: 15px; margin-bottom: 15px; }}
.read-more {{ display: inline-flex; align-items: center; gap: 5px; background: linear-gradient(135deg, #e94560, #c44569); color: #fff; padding: 10px 24px; border-radius: 25px; text-decoration: none; font-weight: 600; font-size: 14px; transition: all 0.3s; box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3); }}
.read-more:hover {{ transform: translateX(5px); box-shadow: 0 6px 20px rgba(233, 69, 96, 0.4); }}
.empty {{ background: #fff; border-radius: 20px; padding: 60px 20px; text-align: center; color: #999; }}
.empty h3 {{ color: #1a1a2e; margin-bottom: 10px; }}
footer {{ text-align: center; padding: 40px 20px; color: rgba(255,255,255,0.7); font-size: 14px; }}
footer a {{ color: #e94560; font-weight: 600; text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}
@media (max-width: 768px) {{
  h1 {{ font-size: 24px; }}
  .post {{ padding: 20px; }}
  .post h2 {{ font-size: 18px; }}
  .header-info {{ flex-direction: column; align-items: flex-start; }}
  header::before {{ display: none; }}
}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>Юридический дайджест</h1>
<p class="subtitle">Актуальные новости по <strong>семейному</strong> и <strong>трудовому</strong> праву РФ</p>
<nav>
<a href="https://серко.рф" target="_blank">← серко.рф</a>
<a href="https://github.com/IvanX888/legal-blog" target="_blank">GitHub</a>
</nav>
<div class="header-info">
<div class="time">🕐 Обновлено: {now} МСК</div>
<div class="weather">🌤️ {weather}</div>
</div>
</header>

<div class="calendar">
<h3>📅 Новости по датам</h3>
{calendar_html if calendar_html else '<span style="color:rgba(255,255,255,0.6)">Пока нет архива</span>'}
</div>

{''.join(posts_html) if posts_html else '<div class="empty"><h3>Пока записей нет</h3><p>Бот собирает новости каждый день в 9:00. Вы можете <a href="https://github.com/IvanX888/legal-blog/actions">запустить его вручную</a> или добавить статью в папку _posts.</p></div>'}

<footer>
<p>© Юридический дайджест | <a href="https://серко.рф" target="_blank">серко.рф</a> | Все материалы взяты из открытых источников</p>
</footer>
</div>
</body>
</html>'''
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("\n✅ index.html сгенерирован")

if __name__ == '__main__':
    print("🚀 Запуск сбора новостей...")
    for url, name in FEEDS:
        fetch_feed(url, name)
    generate_index()
    print("\n🎉 Готово!")
