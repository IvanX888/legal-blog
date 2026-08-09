import feedparser
import requests
import re
import os
from datetime import datetime
from html import unescape
import html as html_module

FEEDS = [
    ('https://rg.ru/xml/index.xml', 'Российская газета'),
    ('https://duma.gov.ru/news/rss/', 'Госдума'),
    ('https://www.garant.ru/news/rss/', 'ГАРАНТ'),
    ('https://pravo.ru/rss/news/', 'Право.ру'),
    ('https://www.rbc.ru/rss/', 'РБК'),
    ('https://www.kommersant.ru/rss/doc.xml', 'Коммерсантъ'),
    ('https://tass.ru/rss/v2.xml', 'ТАСС'),
    ('https://www.interfax.ru/rss.asp', 'Интерфакс'),
    ('https://ria.ru/export/rss2/archive/index.xml', 'РИА Новости'),
    ('https://iz.ru/xml/rss/all.xml', 'Известия'),
]

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
    'заявление на развод', 'развод в одностороннем', 'расторгнуть брак',
    'совместная собственность', 'личная собственность', 'долги супругов',
    'содержание ребенка', 'содержание супруги', 'индексация алиментов',
    'неуплата алиментов', 'задолженность по алиментам', 'лишение родительских',
    'восстановление в родительских правах', 'определение отцовства',
    'оспаривание отцовства', 'брак с иностранцем', 'развод с иностранцем',
    'семейные споры', 'семейный адвокат', 'юрист по разводу',
    'закон о семье', 'статья семейного кодекса', 'ск ск рф',
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
    'работник', 'работодатель', 'зарплата', 'заработная плата', 'труд',
    'кадровый', 'кадры', 'трудовые отношения', 'трудовая дисциплина',
    'восстановление на работе', 'вынужденный прогул', 'компенсация при увольнении',
    'стажировка', 'подработка', 'совместительство', 'внешний совместитель',
    'дистанционная работа', 'удаленная работа', 'гибкий график',
    'трудовая миграция', 'патент', 'разрешение на работу',
    'охрана труда', 'производственная травма', 'несчастный случай на производстве',
    'аттестация рабочих мест', 'спецоценка условий труда', 'соут',
    'трудовая инспекция проверка',
    'иск о восстановлении', 'трудовой иск', 'трудовой суд',
    'статья тк рф', 'статья трудового кодекса', 'тк рф',
    'закон о занятости', 'центр занятости', 'биржа труда',
    'пособие по безработице', 'пособие по беременности', 'пособие по уходу',
    'страховые взносы', 'пенсионные взносы', 'фсс', 'фонд социального страхования',
]

STOPWORDS = [
    'всу', 'украин', 'украина', 'украины', 'спецопераци', 'военн', 'армия',
    'футбол', 'футбольный', 'баскетбол', 'хоккей', 'теннис', 'олимпиад',
    'чемпионат мира', 'чемпионат европы', 'премьер-лига', 'кхл', 'нхл',
    'матч', 'гол', 'судья', 'фифа', 'уефа', 'спорт',
    'санкци', 'биткоин', 'криптовалют', 'блокчейн',
    'нато', 'евросоюз', 'брюссель', 'вашингтон', 'белый дом', 'пентагон',
    'коронавирус', 'covid', 'пандеми',
    'дтп', 'авария на трассе', 'пожар', 'наводнени', 'землетрясени',
    'убийство', 'ограблени', 'кража', 'преступлени', 'убий', 'покушени',
    'беспилотник', 'дрон', 'ракетный удар', 'обстрел', 'взрыв',
    'курс доллара', 'курс евро', 'биржа', 'акции', 'инвестиции',
]

POSTS_DIR = '_posts'
os.makedirs(POSTS_DIR, exist_ok=True)


def normalize(text):
    return unescape(text).lower()


def has_keywords(text, keywords):
    t = normalize(text)
    return any(kw.lower() in t for kw in keywords)


def has_stopwords(text):
    t = normalize(text)
    return any(sw in t for sw in STOPWORDS)


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


def parse_date(entry):
    for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
        if hasattr(entry, field) and getattr(entry, field):
            return datetime(*getattr(entry, field)[:6])
    for field in ['published', 'updated', 'date']:
        if hasattr(entry, field) and getattr(entry, field):
            try:
                return datetime.strptime(getattr(entry, field)[:10], '%Y-%m-%d')
            except:
                pass
    return datetime.now()


def is_recent(entry_date, days=30):
    try:
        delta = datetime.now() - entry_date
        return delta.days <= days
    except:
        return True


def fetch_full_text(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        resp = requests.get(url, headers=headers, timeout=25)
        resp.raise_for_status()
        html = resp.text

        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<noscript[^>]*>.*?</noscript>', '', text, flags=re.DOTALL)

        article_match = re.search(r'<article[^>]*>(.*?)</article>', text, re.DOTALL | re.IGNORECASE)
        main_match = re.search(r'<main[^>]*>(.*?)</main>', text, re.DOTALL | re.IGNORECASE)
        quote_single = chr(39)
        quote_double = chr(34)
        content_match = re.search(
            r'<div[^>]*class=[' + quote_single + quote_double + r'][^' + quote_single + quote_double + r']*(?:content|text|article|news|body)[^' + quote_single + quote_double + r']*[' + quote_single + quote_double + r'][^>]*>(.*?)</div>',
            text, re.DOTALL | re.IGNORECASE
        )

        if article_match:
            content = article_match.group(1)
        elif main_match:
            content = main_match.group(1)
        elif content_match:
            content = content_match.group(1)
        else:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', text, re.DOTALL | re.IGNORECASE)
            content = body_match.group(1) if body_match else text

        content = re.sub(r'<nav[^>]*>.*?</nav>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<footer[^>]*>.*?</footer>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<aside[^>]*>.*?</aside>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<header[^>]*>.*?</header>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<form[^>]*>.*?</form>', '', content, flags=re.DOTALL | re.IGNORECASE)

        content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
        content = re.sub(r'<p[^>]*>', '\n', content, flags=re.IGNORECASE)
        content = re.sub(r'</p>', '\n', content, flags=re.IGNORECASE)
        content = re.sub(r'<[^>]+>', ' ', content)
        content = unescape(content)

        content = re.sub(r'[ \t]+', ' ', content)
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = content.strip()

        content = re.sub(r'^(?:Реклама|Поделиться|Читайте также|Смотрите также|Вам может быть интересно)[\s\S]*?(?=\n\n)', '', content, flags=re.IGNORECASE)

        if len(content) > 12000:
            content = content[:12000].rsplit('\n', 1)[0] + '\n\n[Текст сокращён...]'

        return content
    except Exception as e:
        print(f"  ⚠️ Не удалось распарсить текст: {e}")
        return ""


def text_to_html(text):
    if not text:
        return '<p class="no-fulltext">Полный текст недоступен. Перейдите к источнику.</p>'
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    if not paragraphs:
        return '<p class="no-fulltext">Полный текст недоступен. Перейдите к источнику.</p>'
    return '\n'.join(f'<p>{html_module.escape(p)}</p>' for p in paragraphs)


def create_post(title, link, summary, source, category, full_text=''):
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H-%M-%S')
    slug = slugify(title) or 'news'
    filename = f"{POSTS_DIR}/{date}-{time}-{slug}.md"

    if already_exists(link):
        print(f"  SKIP (exists): {title[:60]}")
        return False

    title_escaped = title.replace('"', '\"')
    now_time = datetime.now().strftime('%H:%M:%S')
    short_summary = truncate(summary, 350)

    content = f"""---
layout: post
title: "{title_escaped}"
date: {date} {now_time} +0300
categories: {category}
source: {source}
link: {link}
---

**Источник:** [{source}]({link})

{short_summary}

<!--more-->

{full_text}
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  CREATED [{category}]: {title[:60]}")
    return True


def fetch_feed(url, source_name):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        print(f"\n📡 {source_name}...")
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        if not feed.entries:
            print(f"  ⚠️  RSS пуст")
            return

        print(f"  Записей в RSS: {len(feed.entries)}")

        found = 0
        checked = 0

        for entry in feed.entries[:25]:
            title = entry.get('title', 'Без названия')
            link = entry.get('link') or ''
            if link and not link.startswith('http'):
                link = ''
            summary = entry.get('summary', entry.get('description', ''))

            entry_date = parse_date(entry)
            if not is_recent(entry_date, days=60):
                continue

            checked += 1
            text = f"{title} {summary}"

            if has_stopwords(text):
                print(f"  SKIP (stopword): {title[:60]}")
                continue

            category = None
            if has_keywords(text, KEYWORDS_FAMILY):
                category = 'семейное-право'
            elif has_keywords(text, KEYWORDS_LABOR):
                category = 'трудовое-право'

            if category:
                full_text = ""
                if link:
                    full_text = fetch_full_text(link)

                # Fallback: if parsing failed, use RSS summary as content
                if not full_text.strip() and summary:
                    clean_summary = re.sub(r'<[^>]+>', '', summary)
                    clean_summary = unescape(clean_summary)
                    full_text = clean_summary
                    print(f"  ⚠️ Парсинг не сработал, используем RSS summary ({len(full_text)} символов)")

                if create_post(title, link, summary, source_name, category, full_text):
                    found += 1

        print(f"  ✅ Проверено свежих: {checked}, найдено по теме: {found}")

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
        full_text = ''

        lines_local = content.split('\n')
        in_frontmatter = False
        frontmatter_done = False
        passed_more = False

        for line in lines_local:
            stripped = line.strip()
            if stripped == '---':
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
                    if link.lower() == 'none':
                        link = ''
                elif line.startswith('source:'):
                    source = line[7:].strip()
                    if source.lower() == 'none':
                        source = ''
            else:
                if stripped == '<!--more-->':
                    passed_more = True
                    continue
                if stripped.startswith('**Источник:**'):
                    continue
                if passed_more:
                    full_text += line + '\n'
                else:
                    if stripped and not stripped.startswith('---'):
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
        full_text = full_text.strip()

        posts.append({
            'title': title,
            'date': date,
            'category': category,
            'source': source,
            'link': link,
            'cat_class': cat_class,
            'summary': short_text,
            'full_text': full_text,
        })

    posts_html = []
    for idx, post in enumerate(posts):
        post_id = "post-" + str(idx)
        valid_link = post['link'] if (post['link'] and post['link'].startswith('http')) else ''
        source_name = post['source'] or 'Источник'

        full_text_html = text_to_html(post['full_text'])

        if valid_link:
            source_footer = '<div class="source-link"><a href="' + valid_link + '" target="_blank" rel="noopener">🔗 Источник: ' + html_module.escape(source_name) + ' &mdash; читать оригинал &rarr;</a></div>'
        else:
            source_footer = '<div class="source-link muted">🔗 Источник недоступен</div>'

        # FIX: не показываем кнопку если нет полного текста
        has_full = bool(post['full_text'].strip())
        if has_full:
            toggle_btn = '<button class="read-more-btn" onclick="toggleFullText(&quot;' + post_id + '&quot;)">Читать полностью &rarr;</button>'
            full_block = '<div class="full-text" id="full-' + post_id + '" style="display:none;">\n<div class="full-text-content">\n' + full_text_html + '\n</div>\n' + source_footer + '\n</div>'
        else:
            toggle_btn = ''
            full_block = ''

        post_html = '<article class="post" id="' + post_id + '">\n'
        post_html += '<h2>' + html_module.escape(post["title"]) + '</h2>\n'
        post_html += '<div class="meta">\n'
        post_html += '<span class="date">📅 ' + post["date"] + '</span>\n'
        post_html += '<span class="badge ' + post["cat_class"] + '">' + post["category"] + '</span>\n'
        post_html += '<span class="source">📰 ' + html_module.escape(post["source"] or "Неизвестный источник") + '</span>\n'
        post_html += '</div>\n'
        post_html += '<p class="excerpt">' + html_module.escape(post["summary"]) + '</p>\n'
        post_html += toggle_btn + '\n'
        post_html += full_block + '\n'
        post_html += '</article>'
        posts_html.append(post_html)

    calendar_html = ''
    for d in sorted(dates, reverse=True)[:15]:
        calendar_html += '<a href="#date-' + d + '" class="cal-date">' + d + '</a>'

    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    weather = get_weather()

    if posts_html:
        posts_block = '\n'.join(posts_html)
    else:
        posts_block = '<div class="empty"><h3>Пока записей нет</h3><p>Бот собирает свежие новости каждый день в 9:00. Вы можете добавить статью в папку _posts.</p></div>'

    html = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Юридический дайджест &mdash; семейное и трудовое право РФ</title>
<meta name="description" content="Актуальные новости по семейному и трудовому праву Российской Федерации. Алименты, развод, трудовые споры, увольнение, декрет.">
<meta name="keywords" content="семейное право, трудовое право, алименты, развод, увольнение, трудовой кодекс, юрист, юридические новости, РФ">
<meta property="og:title" content="Юридический дайджест">
<meta property="og:description" content="Актуальные новости по семейному и трудовому праву РФ">
<meta property="og:type" content="website">
<meta property="og:url" content="https://серко.рф/legal-blog/">
<meta name="robots" content="index, follow">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; color: #333; }
.container { max-width: 1000px; margin: 0 auto; padding: 20px; }
header { background: linear-gradient(135deg, #e94560 0%, #ff6b6b 50%, #c44569 100%); border-radius: 20px; padding: 35px; margin-bottom: 25px; box-shadow: 0 10px 40px rgba(233, 69, 96, 0.3); position: relative; overflow: hidden; }
header::before { content: "\u2696\uFE0F"; position: absolute; right: 30px; top: 50%; transform: translateY(-50%); font-size: 80px; opacity: 0.15; }
h1 { font-size: 32px; color: #fff; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
.subtitle { color: rgba(255,255,255,0.9); font-size: 16px; margin-bottom: 20px; }
.header-info { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2); }
.weather { background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); color: #fff; padding: 10px 20px; border-radius: 25px; font-size: 14px; font-weight: 600; }
.time { color: rgba(255,255,255,0.8); font-size: 14px; }
nav { margin-top: 15px; }
nav a { color: #fff; text-decoration: none; font-weight: 600; margin-right: 25px; opacity: 0.9; transition: opacity 0.2s; }
nav a:hover { opacity: 1; text-decoration: underline; }
.calendar { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; margin-bottom: 25px; }
.calendar h3 { color: #fff; font-size: 16px; margin-bottom: 12px; }
.cal-date { display: inline-block; background: rgba(255,255,255,0.15); color: #fff; padding: 6px 14px; border-radius: 20px; font-size: 13px; margin: 4px; text-decoration: none; transition: all 0.2s; }
.cal-date:hover { background: #e94560; transform: scale(1.05); }
.post { background: #fff; border-radius: 20px; padding: 30px; margin-bottom: 25px; box-shadow: 0 8px 30px rgba(0,0,0,0.15); transition: all 0.3s; border-left: 5px solid transparent; }
.post:hover { transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.2); }
.post:nth-child(3n+1) { border-left-color: #e94560; }
.post:nth-child(3n+2) { border-left-color: #533483; }
.post:nth-child(3n+3) { border-left-color: #0f3460; }
.post h2 { font-size: 22px; color: #1a1a2e; margin-bottom: 15px; line-height: 1.4; }
.meta { display: flex; gap: 15px; flex-wrap: wrap; align-items: center; margin-bottom: 15px; font-size: 14px; color: #666; }
.badge { padding: 5px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.cat-family { background: #fce4ec; color: #c2185b; }
.cat-labor { background: #e8f5e9; color: #2e7d32; }
.excerpt { color: #555; line-height: 1.7; font-size: 15px; margin-bottom: 15px; }
.read-more-btn { display: inline-flex; align-items: center; gap: 5px; background: linear-gradient(135deg, #e94560, #c44569); color: #fff; padding: 10px 24px; border-radius: 25px; border: none; cursor: pointer; font-weight: 600; font-size: 14px; transition: all 0.3s; box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3); }
.read-more-btn:hover { transform: translateX(5px); box-shadow: 0 6px 20px rgba(233, 69, 96, 0.4); }
.full-text { margin-top: 20px; padding-top: 20px; border-top: 2px solid #f0f0f0; display: none; animation: fadeIn 0.3s ease; }
.full-text-content { line-height: 1.8; font-size: 15px; color: #333; }
.full-text-content p { margin-bottom: 15px; }
.no-fulltext { color: #999; font-style: italic; padding: 20px; text-align: center; background: #f9f9f9; border-radius: 10px; }
.source-link { margin-top: 25px; padding: 15px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; text-align: center; border: 1px solid #dee2e6; }
.source-link a { color: #e94560; font-weight: 700; text-decoration: none; font-size: 15px; transition: all 0.2s; }
.source-link a:hover { text-decoration: underline; }
.source-link.muted { color: #999; font-size: 14px; }
.empty { background: #fff; border-radius: 20px; padding: 60px 20px; text-align: center; color: #999; }
.empty h3 { color: #1a1a2e; margin-bottom: 10px; }
footer { text-align: center; padding: 40px 20px; color: rgba(255,255,255,0.7); font-size: 14px; }
footer a { color: #e94560; font-weight: 600; text-decoration: none; }
footer a:hover { text-decoration: underline; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 768px) {
  h1 { font-size: 24px; }
  .post { padding: 20px; }
  .post h2 { font-size: 18px; }
  .header-info { flex-direction: column; align-items: flex-start; }
  header::before { display: none; }
}
</style>
</head>
<body>
<div class="container">
<header>
<h1>Юридический дайджест</h1>
<p class="subtitle">Актуальные новости по <strong>семейному</strong> и <strong>трудовому</strong> праву РФ</p>
<nav>
<a href="https://серко.рф" target="_blank">&larr; серко.рф</a>
</nav>
<div class="header-info">
<div class="time">🕐 Обновлено: """ + now + """ МСК</div>
<div class="weather">🌤️ """ + weather + """</div>
</div>
</header>

<div class="calendar">
<h3>📅 Новости по датам</h3>
""" + (calendar_html if calendar_html else '<span style="color:rgba(255,255,255,0.6)">Пока нет архива</span>') + """
</div>

""" + posts_block + """

<div style="background: linear-gradient(135deg, #e94560, #c44569); border-radius: 20px; padding: 30px; margin: 30px 0; text-align: center; color: white; box-shadow: 0 8px 30px rgba(233, 69, 96, 0.3);">
<h3 style="margin-bottom: 10px; font-size: 22px;">💼 Нужна помощь юриста?</h3>
<p style="margin-bottom: 20px; font-size: 16px; opacity: 0.95;">Составим исковое заявление, договор, консультацию &mdash; быстро и профессионально</p>
<a href="https://серко.рф" target="_blank" style="display: inline-block; background: white; color: #e94560; padding: 14px 35px; border-radius: 30px; text-decoration: none; font-weight: 700; font-size: 16px;">Заказать консультацию &rarr;</a>
</div>

<footer>
<p>&copy; Юридический дайджест | <a href="https://серко.рф" target="_blank">серко.рф</a> | Все материалы взяты из открытых источников</p>
</footer>
</div>

<script>
function toggleFullText(postId) {
    var fullEl = document.getElementById('full-' + postId);
    var btn = fullEl.previousElementSibling;
    if (fullEl.style.display === 'none' || fullEl.style.display === '') {
        fullEl.style.display = 'block';
        btn.textContent = 'Свернуть \u2191';
        setTimeout(function() {
            fullEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 50);
    } else {
        fullEl.style.display = 'none';
        btn.textContent = 'Читать полностью \u2192';
    }
}
</script>
</body>
</html>"""

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("\n✅ index.html сгенерирован")


if __name__ == '__main__':
    print("🚀 Запуск сбора новостей...")
    print("📋 Источники: РГ, Госдума, ГАРАНТ, Право.ру, РБК, Коммерсантъ, ТАСС, Интерфакс, РИА, Известия")
    print("🛡️  Фильтр стоп-слов активен: военные темы, спорт, крипта, ДТП и т.д. отбрасываются")
    for url, name in FEEDS:
        fetch_feed(url, name)
    generate_index()
    print("\n🎉 Готово!")
