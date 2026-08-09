import feedparser
import requests
import re
import html as html_module
import os
from datetime import datetime
import time
import random

POSTS_DIR = '_posts'
os.makedirs(POSTS_DIR, exist_ok=True)

STOPWORDS = [
    'всу', 'украина', 'спецоперация', 'армия', 'беспилотник', 'ракетный удар',
    'футбол', 'хоккей', 'теннис', 'матч', 'гол', 'чемпионат',
    'биткоин', 'биржа', 'курс доллара',
    'авария на трассе', 'убийство', 'пожар',
    'нато', 'евросоюз', 'санкции',
    'мем', 'мемы', 'фото', 'премьер', 'санчес', 'шутка', 'юмор', 'вирусный',
    'ретушь', 'голливуд', 'кино', 'сериал', 'знаменитост', 'шоу', 'концерт',
    'блогер', 'инфлюенсер', 'тикток', 'instagram',
]

KEYWORDS = [
    'алимент', 'развод', 'семейн', 'брак', 'родитель', 'ребенок', 'опека',
    'трудовой', 'увольнение', 'работник', 'работодатель', 'зарплат', 'отпуск',
    'декрет', 'индексация', 'мрот', 'штраф', 'иск', 'суд', 'юрист', 'закон',
    'кодекс', 'право', 'договор', 'наследство', 'выселение', 'прописка',
    'субсидия', 'пособие', 'пенсия', 'налог', 'ипотека', 'кредит', 'долг',
    'арест', 'судебн', 'пристав', 'исполнительн', 'жалоба', 'апелляц',
    'заявление', 'ходатайство', 'нотариус', 'регистрац', 'лиценз', 'страхов',
]

RSS_URLS = [
    'https://www.rbc.ru/legal/rss/feed',
    'https://www.kommersant.ru/doc/rss?type=100',
    'https://tass.ru/rss/v2.xml?sections=NDczMw%3D%3D',
    'https://rg.ru/rss/index.xml',
    'https://lenta.ru/rss/news',
]


def clean_html(raw_html):
    if not raw_html:
        return ''
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = re.sub(r'\s+', ' ', text).strip()
    text = html_module.unescape(text)
    return text


def truncate(text, length=300):
    if not text:
        return ''
    if len(text) <= length:
        return text
    truncated = text[:length]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + '...'


def text_to_html(text):
    if not text or not text.strip():
        return '<p class="no-fulltext">Полный текст недоступен</p>'
    paragraphs = text.split('\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if p:
            p = html_module.escape(p)
            p = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p)
            p = re.sub(r'\*(.+?)\*', r'<em>\1</em>', p)
            html_parts.append('<p>' + p + '</p>')
    return '\n'.join(html_parts) if html_parts else '<p class="no-fulltext">Полный текст недоступен</p>'


def get_weather():
    return 'Погода в Нижнем Новгороде: +22°C, облачно'


def fetch_full_text(url):
    if not url or not url.startswith('http'):
        return ''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        html = resp.text

        # Удаляем скрипты, стили, навигацию, футеры, сайдбары
        html = re.sub(r'<(script|style|noscript|iframe|nav|aside|footer|header|form|button|select|textarea)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Ищем основной контент
        content = ''
        for pattern in [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*\bclass\s*=\s*["\'][^"\']*(?:content|article|text|body|main|entry|post|news-text|story-body)[^"\']*["\'][^>]*>(.*?)</div>',
            r'<main[^>]*>(.*?)</main>',
            r'<div[^>]*\brole\s*=\s*["\']main["\'][^>]*>(.*?)</div>',
            r'<section[^>]*\bclass\s*=\s*["\'][^"\']*(?:content|article|text)[^"\']*["\'][^>]*>(.*?)</section>',
        ]:
            m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if m:
                content = m.group(1)
                break

        if not content:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1)

        if not content:
            return ''

        # Удаляем мусорные блоки по классам/id
        content = re.sub(r'<div[^>]*\bclass\s*=\s*["\'][^"\']*(?:share|social|related|tags|comments|author|advert|sidebar|menu|subscribe|newsletter|popup|modal|cookie|banner|promo|recommend|read-more|pagination|toolbar|action-bar|vote|rating|breadcrumbs)[^"\']*["\'][^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<ul[^>]*\bclass\s*=\s*["\'][^"\']*(?:share|social|tags|menu|nav)[^"\']*["\'][^>]*>.*?</ul>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<span[^>]*\bclass\s*=\s*["\'][^"\']*(?:share|social|tag|label|badge)[^"\']*["\'][^>]*>.*?</span>', '', content, flags=re.DOTALL | re.IGNORECASE)

        text = clean_html(content)

        # Проверка на мусорные фразы
        garbage_phrases = ['поделиться', 'читайте также', 'рекомендуем', 'похожие статьи', 'комментарии', 'оставить комментарий', 'войдите', 'зарегистрируйтесь', 'подпишитесь', 'рассылка', 'копирайт', 'все права защищены', 'выделить главное', 'телеканал', 'доступен в пакетах']
        lower_text = text.lower()
        garbage_score = sum(1 for phrase in garbage_phrases if phrase in lower_text)
        if garbage_score > 3:
            return ''

        if len(text) < 200:
            return ''

        return text
    except Exception as e:
        print(f"  ⚠️ Не удалось спарсить {url}: {e}")
        return ''


def fetch_feed(url):
    print(f"\n📡 {url}")
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries[:15]:
            title = entry.get('title', '')
            link = entry.get('link', '') or ''
            summary = entry.get('summary', '') or entry.get('description', '') or ''
            published = entry.get('published', '')

            clean_summary = re.sub(r'<[^>]+>', '', summary)
            clean_summary = html_module.unescape(clean_summary)

            combined = (title + ' ' + clean_summary).lower()
            if any(sw in combined for sw in STOPWORDS):
                continue

            # Title должен содержать хотя бы одно ключевое слово
            title_lower = title.lower()
            if not any(kw in title_lower for kw in KEYWORDS):
                summary_matches = sum(1 for kw in KEYWORDS if kw in combined)
                if summary_matches < 2:
                    continue

            full_text = fetch_full_text(link)

            # Если спарсенный текст равен анонсу — парсинг не сработал
            if full_text.strip() == clean_summary.strip():
                full_text = ''

            # Fallback на RSS-текст
            if not full_text.strip() and clean_summary:
                full_text = clean_summary

            entries.append({
                'title': title,
                'link': link,
                'summary': clean_summary,
                'full_text': full_text,
                'published': published,
            })
            print(f"  ✅ {title[:60]}...")
            time.sleep(random.uniform(0.5, 1.5))
        return entries
    except Exception as e:
        print(f"  ❌ Ошибка RSS: {e}")
        return []


def already_exists(link):
    if not link:
        return False
    for fname in os.listdir(POSTS_DIR):
        if fname.endswith('.md'):
            path = os.path.join(POSTS_DIR, fname)
            with open(path, 'r', encoding='utf-8') as f:
                head = ''.join(f.readline() for _ in range(10))
                if link in head:
                    return True
    return False


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:50].strip('-')


def determine_category(text):
    t = text.lower()
    if any(w in t for w in ['алимент', 'развод', 'семейн', 'брак', 'родитель', 'ребенок', 'опека', 'выселение', 'прописка', 'наследство']):
        return 'семейное право'
    elif any(w in t for w in ['трудовой', 'увольнение', 'работник', 'работодатель', 'зарплат', 'отпуск', 'декрет', 'мрот']):
        return 'трудовое право'
    else:
        return 'юридические новости'


def save_post(entry):
    link = entry.get('link', '')
    if already_exists(link):
        print(f"  ⏭ Уже есть: {entry['title'][:50]}")
        return False

    title = entry['title']
    category = determine_category(title + ' ' + entry.get('summary', ''))
    date_str = datetime.now().strftime('%Y-%m-%d')
    slug = slugify(title)
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    summary = entry.get('summary', '')
    full_text = entry.get('full_text', '')

    lines = [
        '---',
        f'title: "{title}"',
        f'date: {date_str}',
        f'categories: {category}',
        f'link: {link}',
        f'source: {link}',
        '---',
        '',
    ]
    if link:
        lines.append(f'**Источник:** [{link}]({link})')
        lines.append('')
    lines.append(summary)
    lines.append('')
    lines.append('<!--more-->')
    lines.append('')
    lines.append(full_text)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  💾 Сохранено: {filename}")
    return True


def generate_index():
    posts = []
    dates = set()

    for fname in sorted(os.listdir(POSTS_DIR), reverse=True):
        if not fname.endswith('.md'):
            continue
        path = os.path.join(POSTS_DIR, fname)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        title = 'Без названия'
        date = ''
        category = ''
        link = ''
        source = ''
        summary = ''
        full_text = ''

        # Надёжный парсинг: разделяем по первым двум ---
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            body = parts[2]
        else:
            frontmatter = ''
            body = content

        # Парсим frontmatter
        for line in frontmatter.split('\n'):
            line = line.strip()
            if line.startswith('title:'):
                title = line[6:].strip().strip('"').strip("'")
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

        # Парсим body
        body = body.strip()
        if '<!--more-->' in body:
            before, after = body.split('<!--more-->', 1)
            summary_lines = []
            for line in before.split('\n'):
                stripped = line.strip()
                if stripped and not stripped.startswith('**Источник:**'):
                    summary_lines.append(stripped)
            summary = ' '.join(summary_lines)
            full_text = after.strip()
        else:
            body_lines = []
            for line in body.split('\n'):
                stripped = line.strip()
                if stripped and not stripped.startswith('**Источник:**'):
                    body_lines.append(stripped)
            full_text = '\n'.join(body_lines)
            summary = truncate(full_text, 300)

        if date:
            dates.add(date)

        cat_class = 'cat-family' if 'семейное' in category else ('cat-labor' if 'трудовое' in category else 'cat-general')

        # Если полный текст равен анонсу — смысла в кнопке нет
        has_full = bool(full_text.strip()) and full_text.strip() != summary.strip()

        posts.append({
            'title': title,
            'date': date,
            'category': category,
            'source': source or link,
            'link': link,
            'cat_class': cat_class,
            'summary': summary.strip(),
            'full_text': full_text.strip(),
            'has_full': has_full,
        })

    # Генерация HTML
    import io
    out = io.StringIO()
    NL = '\n'

    out.write('<!DOCTYPE html>' + NL)
    out.write('<html lang="ru">' + NL)
    out.write('<head>' + NL)
    out.write('<meta charset="UTF-8">' + NL)
    out.write('<meta name="viewport" content="width=device-width, initial-scale=1.0">' + NL)
    out.write('<title>Юридический дайджест — семейное и трудовое право РФ</title>' + NL)
    out.write('<meta name="description" content="Актуальные новости по семейному и трудовому праву Российской Федерации.">' + NL)
    out.write('<meta name="keywords" content="семейное право, трудовое право, алименты, развод, юрист, юридические новости, РФ">' + NL)
    out.write('<meta property="og:title" content="Юридический дайджест">' + NL)
    out.write('<meta property="og:description" content="Актуальные новости по семейному и трудовому праву РФ">' + NL)
    out.write('<meta property="og:type" content="website">' + NL)
    out.write('<meta property="og:url" content="https://серко.рф/legal-blog/">' + NL)
    out.write('<meta name="robots" content="index, follow">' + NL)
    out.write('<style>' + NL)
    out.write('* { margin: 0; padding: 0; box-sizing: border-box; }' + NL)
    out.write('body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; color: #333; }' + NL)
    out.write('.container { max-width: 1000px; margin: 0 auto; padding: 20px; }' + NL)
    out.write('header { background: linear-gradient(135deg, #e94560 0%, #ff6b6b 50%, #c44569 100%); border-radius: 20px; padding: 35px; margin-bottom: 25px; box-shadow: 0 10px 40px rgba(233, 69, 96, 0.3); position: relative; overflow: hidden; }' + NL)
    out.write('header::before { content: "\\u2696\\uFE0F"; position: absolute; right: 30px; top: 50%; transform: translateY(-50%); font-size: 80px; opacity: 0.15; }' + NL)
    out.write('h1 { font-size: 32px; color: #fff; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }' + NL)
    out.write('.subtitle { color: rgba(255,255,255,0.9); font-size: 16px; margin-bottom: 20px; }' + NL)
    out.write('.header-info { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2); }' + NL)
    out.write('.weather { background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); color: #fff; padding: 10px 20px; border-radius: 25px; font-size: 14px; font-weight: 600; }' + NL)
    out.write('.time { color: rgba(255,255,255,0.8); font-size: 14px; }' + NL)
    out.write('nav { margin-top: 15px; }' + NL)
    out.write('nav a { color: #fff; text-decoration: none; font-weight: 600; margin-right: 25px; opacity: 0.9; transition: opacity 0.2s; }' + NL)
    out.write('nav a:hover { opacity: 1; text-decoration: underline; }' + NL)
    out.write('.calendar { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; margin-bottom: 25px; }' + NL)
    out.write('.calendar h3 { color: #fff; font-size: 16px; margin-bottom: 12px; }' + NL)
    out.write('.cal-date { display: inline-block; background: rgba(255,255,255,0.15); color: #fff; padding: 6px 14px; border-radius: 20px; font-size: 13px; margin: 4px; text-decoration: none; transition: all 0.2s; }' + NL)
    out.write('.cal-date:hover { background: #e94560; transform: scale(1.05); }' + NL)
    out.write('.post { background: #fff; border-radius: 20px; padding: 30px; margin-bottom: 25px; box-shadow: 0 8px 30px rgba(0,0,0,0.15); transition: all 0.3s; border-left: 5px solid transparent; }' + NL)
    out.write('.post:hover { transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.2); }' + NL)
    out.write('.post:nth-child(3n+1) { border-left-color: #e94560; }' + NL)
    out.write('.post:nth-child(3n+2) { border-left-color: #533483; }' + NL)
    out.write('.post:nth-child(3n+3) { border-left-color: #0f3460; }' + NL)
    out.write('.post h2 { font-size: 22px; color: #1a1a2e; margin-bottom: 15px; line-height: 1.4; }' + NL)
    out.write('.meta { display: flex; gap: 15px; flex-wrap: wrap; align-items: center; margin-bottom: 15px; font-size: 14px; color: #666; }' + NL)
    out.write('.badge { padding: 5px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }' + NL)
    out.write('.cat-family { background: #fce4ec; color: #c2185b; }' + NL)
    out.write('.cat-labor { background: #e8f5e9; color: #2e7d32; }' + NL)
    out.write('.cat-general { background: #e3f2fd; color: #1565c0; }' + NL)
    out.write('.excerpt { color: #555; line-height: 1.7; font-size: 15px; margin-bottom: 15px; }' + NL)
    out.write('.read-more-btn { display: inline-flex; align-items: center; gap: 5px; background: linear-gradient(135deg, #e94560, #c44569); color: #fff; padding: 10px 24px; border-radius: 25px; border: none; cursor: pointer; font-weight: 600; font-size: 14px; transition: all 0.3s; box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3); }' + NL)
    out.write('.read-more-btn:hover { transform: translateX(5px); box-shadow: 0 6px 20px rgba(233, 69, 96, 0.4); }' + NL)
    out.write('.full-text { margin-top: 20px; padding-top: 20px; border-top: 2px solid #f0f0f0; display: none; animation: fadeIn 0.3s ease; }' + NL)
    out.write('.full-text-content { line-height: 1.8; font-size: 15px; color: #333; }' + NL)
    out.write('.full-text-content p { margin-bottom: 15px; }' + NL)
    out.write('.no-fulltext { color: #999; font-style: italic; padding: 20px; text-align: center; background: #f9f9f9; border-radius: 10px; }' + NL)
    out.write('.source-link { margin-top: 25px; padding: 15px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; text-align: center; border: 1px solid #dee2e6; }' + NL)
    out.write('.source-link a { color: #e94560; font-weight: 700; text-decoration: none; font-size: 15px; transition: all 0.2s; }' + NL)
    out.write('.source-link a:hover { text-decoration: underline; }' + NL)
    out.write('.source-link.muted { color: #999; font-size: 14px; }' + NL)
    out.write('.empty { background: #fff; border-radius: 20px; padding: 60px 20px; text-align: center; color: #999; }' + NL)
    out.write('.empty h3 { color: #1a1a2e; margin-bottom: 10px; }' + NL)
    out.write('footer { text-align: center; padding: 40px 20px; color: rgba(255,255,255,0.7); font-size: 14px; }' + NL)
    out.write('footer a { color: #e94560; font-weight: 600; text-decoration: none; }' + NL)
    out.write('footer a:hover { text-decoration: underline; }' + NL)
    out.write('@keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }' + NL)
    out.write('@media (max-width: 768px) {' + NL)
    out.write('  h1 { font-size: 24px; }' + NL)
    out.write('  .post { padding: 20px; }' + NL)
    out.write('  .post h2 { font-size: 18px; }' + NL)
    out.write('  .header-info { flex-direction: column; align-items: flex-start; }' + NL)
    out.write('  header::before { display: none; }' + NL)
    out.write('}' + NL)
    out.write('</style>' + NL)
    out.write('</head>' + NL)
    out.write('<body>' + NL)
    out.write('<div class="container">' + NL)
    out.write('<header>' + NL)
    out.write('<h1>Юридический дайджест</h1>' + NL)
    out.write('<p class="subtitle">Актуальные новости по <strong>семейному</strong> и <strong>трудовому</strong> праву РФ</p>' + NL)
    out.write('<nav>' + NL)
    out.write('<a href="https://серко.рф" target="_blank">&larr; серко.рф</a>' + NL)
    out.write('</nav>' + NL)
    out.write('<div class="header-info">' + NL)
    out.write('<div class="time">🕐 Обновлено: ' + datetime.now().strftime('%d.%m.%Y %H:%M') + ' МСК</div>' + NL)
    out.write('<div class="weather">🌤️ ' + get_weather() + '</div>' + NL)
    out.write('</div>' + NL)
    out.write('</header>' + NL)
    out.write(NL)
    out.write('<div class="calendar">' + NL)
    out.write('<h3>📅 Новости по датам</h3>' + NL)

    calendar_html = ''
    for d in sorted(dates, reverse=True)[:15]:
        calendar_html += '<a href="#date-' + d + '" class="cal-date">' + d + '</a>'
    out.write(calendar_html if calendar_html else '<span style="color:rgba(255,255,255,0.6)">Пока нет архива</span>' + NL)
    out.write('</div>' + NL)
    out.write(NL)

    if not posts:
        out.write('<div class="empty"><h3>Пока записей нет</h3><p>Бот собирает свежие новости каждый день в 9:00. Вы можете добавить статью в папку _posts.</p></div>' + NL)
    else:
        for idx, post in enumerate(posts):
            post_id = "post-" + str(idx)
            valid_link = post['link'] if (post['link'] and post['link'].startswith('http')) else ''
            source_name = post['source'] or 'Источник'
            full_text_html = text_to_html(post['full_text'])
            has_full = post['has_full']

            if valid_link:
                source_footer = '<div class="source-link"><a href="' + valid_link + '" target="_blank" rel="noopener">🔗 Источник: ' + html_module.escape(source_name) + ' &mdash; читать оригинал &rarr;</a></div>'
            else:
                source_footer = '<div class="source-link muted">🔗 Источник недоступен</div>'

            out.write('<article class="post" id="' + post_id + '">' + NL)
            out.write('<h2>' + html_module.escape(post["title"]) + '</h2>' + NL)
            out.write('<div class="meta">' + NL)
            out.write('<span class="date">📅 ' + post["date"] + '</span>' + NL)
            out.write('<span class="badge ' + post["cat_class"] + '">' + post["category"] + '</span>' + NL)
            out.write('<span class="source">📰 ' + html_module.escape(post["source"] or "Неизвестный источник") + '</span>' + NL)
            out.write('</div>' + NL)
            out.write('<p class="excerpt">' + html_module.escape(post["summary"]) + '</p>' + NL)
            if has_full:
                out.write('<button class="read-more-btn" onclick="toggleFullText(\'' + post_id + '\')">Читать полностью &rarr;</button>' + NL)
                out.write('<div class="full-text" id="full-' + post_id + '" style="display:none;">' + NL)
                out.write('<div class="full-text-content">' + NL + full_text_html + NL + '</div>' + NL)
                out.write(source_footer + NL)
                out.write('</div>' + NL)
            out.write('</article>' + NL)

    out.write(NL)
    out.write('<div style="background: linear-gradient(135deg, #e94560, #c44569); border-radius: 20px; padding: 30px; margin: 30px 0; text-align: center; color: white; box-shadow: 0 8px 30px rgba(233, 69, 96, 0.3);">' + NL)
    out.write('<h3 style="margin-bottom: 10px; font-size: 22px;">💼 Нужна помощь юриста?</h3>' + NL)
    out.write('<p style="margin-bottom: 20px; font-size: 16px; opacity: 0.95;">Составим исковое заявление, договор, консультацию &mdash; быстро и профессионально</p>' + NL)
    out.write('<a href="https://серко.рф" target="_blank" style="display: inline-block; background: white; color: #e94560; padding: 14px 35px; border-radius: 30px; text-decoration: none; font-weight: 700; font-size: 16px;">Заказать консультацию &rarr;</a>' + NL)
    out.write('</div>' + NL)
    out.write(NL)
    out.write('<footer>' + NL)
    out.write('<p>&copy; Юридический дайджест | <a href="https://серко.рф" target="_blank">серко.рф</a> | Все материалы взяты из открытых источников</p>' + NL)
    out.write('</footer>' + NL)
    out.write('</div>' + NL)
    out.write(NL)
    out.write('<script>' + NL)
    out.write('function toggleFullText(postId) {' + NL)
    out.write('    var fullEl = document.getElementById("full-" + postId);' + NL)
    out.write('    var btn = document.querySelector("#" + postId + " .read-more-btn");' + NL)
    out.write('    if (fullEl.style.display === "none" || fullEl.style.display === "") {' + NL)
    out.write('        fullEl.style.display = "block";' + NL)
    out.write('        btn.textContent = "Свернуть \\u2191";' + NL)
    out.write('        setTimeout(function() {' + NL)
    out.write('            fullEl.scrollIntoView({ behavior: "smooth", block: "nearest" });' + NL)
    out.write('        }, 50);' + NL)
    out.write('    } else {' + NL)
    out.write('        fullEl.style.display = "none";' + NL)
    out.write('        btn.textContent = "Читать полностью \\u2192";' + NL)
    out.write('    }' + NL)
    out.write('}' + NL)
    out.write('</script>' + NL)
    out.write('</body>' + NL)
    out.write('</html>' + NL)

    html = out.getvalue()
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("\n✅ index.html сгенерирован")


if __name__ == '__main__':
    print("=" * 50)
    print("ЮРИДИЧЕСКИЙ ДАЙДЖЕСТ v2.1")
    print("=" * 50)

    all_entries = []
    for url in RSS_URLS:
        entries = fetch_feed(url)
        all_entries.extend(entries)

    print(f"\n📊 Всего найдено: {len(all_entries)} записей")

    saved = 0
    for entry in all_entries:
        if save_post(entry):
            saved += 1

    print(f"\n💾 Сохранено новых: {saved}")
    generate_index()
    print("\n🎉 Готово! Откройте index.html в браузере.")
