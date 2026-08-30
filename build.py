#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime

SITE_URL = "https://серко.рф"
BLOG_PATH = "/legal-blog"
POSTS_DIR = "_posts"
TEMPLATE_FILE = "_template.html"
OUTPUT_DIR = "."

def parse_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1].strip()
    content = parts[2].strip()
    meta = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            meta[key] = val
    return meta, content

def slug_from_filename(filename):
    name = os.path.splitext(filename)[0]
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name) + ".html"

def date_ru(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    except:
        return date_str

def build_posts():
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    posts = []
    for filename in sorted(os.listdir(POSTS_DIR), reverse=True):
        if not filename.endswith(".md"):
            continue
        with open(os.path.join(POSTS_DIR, filename), "r", encoding="utf-8") as f:
            text = f.read()
        meta, content = parse_front_matter(text)
        slug = slug_from_filename(filename)
        title = meta.get("title", "Без заголовка")
        description = meta.get("description", "")
        category = meta.get("category", "общее")
        date = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
        canonical = SITE_URL + BLOG_PATH + "/" + slug
        html = template
        html = html.replace("{{title}}", title)
        html = html.replace("{{description}}", description)
        html = html.replace("{{category}}", category)
        html = html.replace("{{date}}", date)
        html = html.replace("{{date_ru}}", date_ru(date))
        html = html.replace("{{canonical}}", canonical)
        html = html.replace("{{content}}", content)
        with open(os.path.join(OUTPUT_DIR, slug), "w", encoding="utf-8") as f:
            f.write(html)
        text_only = re.sub(r"<[^>]+>", "", content)
        teaser = text_only[:300] + "..." if len(text_only) > 300 else text_only
        posts.append({
            "title": title, "slug": slug, "date": date,
            "date_ru": date_ru(date), "category": category,
            "teaser": teaser, "canonical": canonical,
            "description": description
        })
        print("[OK] " + slug)
    return posts

def build_index(posts):
    cards = []
    for i, p in enumerate(posts):
        border_color = ["#e94560", "#533483", "#0f3460"][i % 3]
        card = (
            '<article class="post" id="post-' + str(i) + '" style="border-left-color:' + border_color + '">\n'
            '  <h2>' + p["title"] + '</h2>\n'
            '  <div class="meta">\n'
            '    <span class="date">📅 ' + p["date_ru"] + '</span>\n'
            '    <span class="badge cat-family">' + p["category"] + '</span>\n'
            '    <span class="source">📰 Материал подготовлен юристом Серко И.И.</span>\n'
            '  </div>\n'
            '  <p class="excerpt">' + p["teaser"] + '</p>\n'
            '  <a href="' + p["slug"] + '" class="read-more-btn">Читать полностью →</a>\n'
            '</article>'
        )
        cards.append(card)
    cards_html = "\n".join(cards) if cards else '<div class="empty"><h3>Посты скоро появятся...</h3></div>'

    cal_dates = "\n".join(['<a href="#' + p["slug"].replace('.html', '') + '" class="cal-date">' + p["date"] + '</a>' for p in posts])

    html = (
        '<!DOCTYPE html>\n<html lang="ru">\n<head>\n'
        '<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>Юридический дайджест - семейное и трудовое право РФ | Серко И.И.</title>\n'
        '<meta name="description" content="Актуальные новости по семейному и трудовому праву РФ. Юрист Серко Иван Иванович.">\n'
        '<meta name="robots" content="index, follow">\n'
        '<link rel="canonical" href="' + SITE_URL + BLOG_PATH + '/">\n'
        '<meta property="og:title" content="Юридический дайджест | Серко И.И.">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:url" content="' + SITE_URL + BLOG_PATH + '/">\n'
        '<script type="application/ld+json">\n'
        '{"@context":"https://schema.org","@type":"Blog","name":"Юридический дайджест - Серко И.И.",'
        '"url":"' + SITE_URL + BLOG_PATH + '/","author":{"@type":"Person","name":"Серко Иван Иванович",'
        '"url":"' + SITE_URL + '/","sameAs":["https://t.me/BYIvanko","https://t.me/ConsulLexbot"]},'
        '"publisher":{"@type":"Organization","name":"Серко И.И. - юрист онлайн"}}\n'
        '</script>\n'
        '<!-- Yandex.Metrika counter -->\n'
        '<script type="text/javascript">(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};'
        'm[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}'
        'k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})'
        '(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");'
        'ym(111837018,"init",{clickmap:true,trackLinks:true,accurateTrackBounce:true});</script>\n'
        '<noscript><div><img src="https://mc.yandex.ru/watch/111837018" style="position:absolute;left:-9999px;" alt="" /></div></noscript>\n'
        '<style>\n' + open('_style.css', 'r', encoding='utf-8').read() + '\n'
        '.post a.read-more-btn { text-decoration: none; }\n'
        '</style>\n</head>\n<body>\n'
        '<div class="sticky-bar">\n'
        '  <a href="https://t.me/ConsulLexbot" class="btn-bot" target="_blank" rel="noopener noreferrer">🤖 Написать боту</a>\n'
        '  <a href="tel:+79774232473" class="btn-call">📞 Позвонить</a>\n'
        '</div>\n'
        '<div class="container">\n'
        '<header>\n<h1>Юридический дайджест</h1>\n'
        '<p class="subtitle">Актуальные новости по <strong>семейному</strong> и <strong>трудовому</strong> праву РФ</p>\n'
        '<nav>\n<a href="' + SITE_URL + '" target="_blank">← серко.рф</a>\n'
        '<a href="https://t.me/ConsulLexbot" target="_blank" rel="noopener noreferrer">🤖 Бот</a>\n'
        '</nav>\n'
        '<div class="header-info">\n'
        '<div class="time">⏰ Обновлено: ' + datetime.now().strftime("%d.%m.%Y %H:%M") + ' МСК</div>\n'
        '<div class="weather">🌤 Москва: +22°C</div>\n'
        '</div>\n</header>\n\n'
        '<div class="calendar">\n<h3>📅 Новости по датам</h3>\n' + cal_dates + '\n</div>\n\n'
        + cards_html + '\n\n'
        '<div class="footer-cta">\n'
        '<h3>💼 Нужна помощь юриста?</h3>\n'
        '<p>Составим иск, договор, консультацию — быстро и профессионально</p>\n'
        '<div class="cta-buttons">\n'
        '<a href="https://t.me/ConsulLexbot" class="btn-bot" target="_blank" rel="noopener noreferrer">🤖 Написать боту</a>\n'
        '<a href="' + SITE_URL + '" class="btn-site" target="_blank">🌐 Перейти на сайт</a>\n'
        '</div>\n</div>\n\n'
        '<footer>\n'
        '<p>© Юридический дайджест | <a href="' + SITE_URL + '" target="_blank">серко.рф</a> | '
        '<a href="https://t.me/ConsulLexbot" target="_blank" rel="noopener noreferrer">@ConsulLexbot</a> | '
        'Все материалы взяты из открытых источников</p>\n'
        '</footer>\n</div>\n</body>\n</html>'
    )
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("[OK] index.html")

def build_sitemap(posts):
    urls = [
        '<url><loc>' + SITE_URL + BLOG_PATH + '/</loc><lastmod>' + datetime.now().strftime("%Y-%m-%d") + '</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>'
    ]
    for p in posts:
        urls.append('<url><loc>' + p["canonical"] + '</loc><lastmod>' + p["date"] + '</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + '\n</urlset>'
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    print("[OK] sitemap.xml")

def build_robots():
    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: " + SITE_URL + BLOG_PATH + "/sitemap.xml")
    print("[OK] robots.txt")

if __name__ == "__main__":
    print("=" * 40 + "\n  СБОРКА БЛОГА\n" + "=" * 40)
    posts = build_posts()
    build_index(posts)
    build_sitemap(posts)
    build_robots()
    print("=" * 40)
    print("Готово! Постов: " + str(len(posts)))
