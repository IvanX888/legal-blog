#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт автоматической сборки блога.
Запускайте перед каждым коммитом: python build.py
Или настройте GitHub Actions для автозапуска.

Что делает:
1. Читает все посты из папки _posts/
2. Генерирует отдельные HTML-страницы для каждого поста
3. Обновляет index.html (главную с анонсами)
4. Обновляет sitemap.xml
5. Обновляет robots.txt

Как добавить новый пост:
1. Создайте файл _posts/YYYY-MM-DD-slug.md
2. В начале файла - front matter (между ---):
   ---
   title: "Заголовок поста"
   description: "Описание для SEO"
   category: "семейное право"
   date: "2026-08-30"
   ---
3. После --- пишите контент в HTML
4. Запустите: python build.py
5. Закоммитьте и запушьте
"""

import os
import re
from datetime import datetime

# ==========================================
# НАСТРОЙКИ
# ==========================================
SITE_URL = "https://серко.рф"
BLOG_PATH = "/legal-blog"
POSTS_DIR = "_posts"
TEMPLATE_FILE = "_template.html"
OUTPUT_DIR = "."

# ==========================================
# ФУНКЦИИ
# ==========================================

def parse_front_matter(text):
    """Парсит YAML front matter из markdown-файла"""
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
    """2026-08-09-kak-vyselit.md -> kak-vyselit.html"""
    name = os.path.splitext(filename)[0]
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)
    return slug + ".html"

def date_ru(date_str):
    """2026-08-09 -> 09.08.2026"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%d.%m.%Y")
    except:
        return date_str

def build_posts():
    """Генерирует отдельные HTML-страницы для каждого поста"""
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    posts = []

    for filename in sorted(os.listdir(POSTS_DIR), reverse=True):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
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

        out_path = os.path.join(OUTPUT_DIR, slug)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        text_only = re.sub(r"<[^>]+>", "", content)
        teaser = text_only[:300] + "..." if len(text_only) > 300 else text_only

        posts.append({
            "title": title,
            "slug": slug,
            "date": date,
            "date_ru": date_ru(date),
            "category": category,
            "teaser": teaser,
            "canonical": canonical,
        })

        print("[OK] Сгенерирован: " + slug)

    return posts

def build_index(posts):
    """Генерирует главную страницу блога с анонсами"""

    cards = []
    for p in posts:
        card = (
            '<div class="post-card">\n'
            '  <div class="post-meta">\n'
            '    <span class="post-date">' + p["date_ru"] + '</span>\n'
            '    <span class="post-badge">' + p["category"] + '</span>\n'
            '  </div>\n'
            '  <h2 class="post-title"><a href="' + p["slug"] + '">' + p["title"] + '</a></h2>\n'
            '  <p class="post-teaser">' + p["teaser"] + '</p>\n'
            '  <a href="' + p["slug"] + '" class="post-link">Читать полностью &rarr;</a>\n'
            '</div>'
        )
        cards.append(card)

    cards_html = "\n".join(cards) if cards else "<p>Посты скоро появятся...</p>"

    html = (
        '<!DOCTYPE html>\n'
        '<html lang="ru">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>Юридический дайджест | Блог юриста Серко И.И.</title>\n'
        '<meta name="description" content="Актуальные новости по семейному и трудовому праву РФ. Юрист Серко И.И. - алименты, развод, выселение, трудовые споры.">\n'
        '<meta name="robots" content="index, follow">\n'
        '<link rel="canonical" href="' + SITE_URL + BLOG_PATH + '/">\n'
        '<meta property="og:title" content="Юридический дайджест">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:url" content="' + SITE_URL + BLOG_PATH + '/">\n'
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "Blog",\n'
        '  "name": "Юридический дайджест",\n'
        '  "url": "' + SITE_URL + BLOG_PATH + '/",\n'
        '  "author": {\n'
        '    "@type": "Person",\n'
        '    "name": "Серко Иван Иванович",\n'
        '    "url": "' + SITE_URL + '/"\n'
        '  }\n'
        '}\n'
        '</script>\n'
        '<style>\n'
        '* { margin: 0; padding: 0; box-sizing: border-box; }\n'
        'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; color: #333; padding-bottom: 80px; }\n'
        '.container { max-width: 900px; margin: 0 auto; padding: 20px; }\n'
        'header { background: linear-gradient(135deg, #e94560 0%, #ff6b6b 50%, #c44569 100%); border-radius: 20px; padding: 40px; margin-bottom: 30px; text-align: center; }\n'
        'header h1 { font-size: 32px; color: #fff; margin-bottom: 10px; }\n'
        'header p { color: rgba(255,255,255,0.9); font-size: 16px; }\n'
        'header nav { margin-top: 20px; }\n'
        'header nav a { color: #fff; text-decoration: none; font-weight: 600; margin: 0 15px; padding: 8px 20px; border: 2px solid rgba(255,255,255,0.3); border-radius: 25px; transition: all 0.3s; }\n'
        'header nav a:hover { background: rgba(255,255,255,0.2); }\n'
        '.post-card { background: #fff; border-radius: 20px; padding: 30px; margin-bottom: 25px; box-shadow: 0 8px 30px rgba(0,0,0,0.15); transition: transform 0.2s; }\n'
        '.post-card:hover { transform: translateY(-3px); }\n'
        '.post-meta { display: flex; gap: 15px; align-items: center; margin-bottom: 15px; font-size: 13px; color: #888; }\n'
        '.post-date { color: #666; }\n'
        '.post-badge { padding: 4px 12px; border-radius: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase; background: #fce4ec; color: #c2185b; }\n'
        '.post-title { font-size: 22px; margin-bottom: 12px; }\n'
        '.post-title a { color: #1a1a2e; text-decoration: none; }\n'
        '.post-title a:hover { color: #e94560; }\n'
        '.post-teaser { line-height: 1.7; color: #555; margin-bottom: 15px; }\n'
        '.post-link { color: #e94560; font-weight: 700; text-decoration: none; }\n'
        '.post-link:hover { text-decoration: underline; }\n'
        '.cta-block { background: linear-gradient(135deg,#f8f9fa,#e9ecef); border-radius: 20px; padding: 35px; margin-top: 40px; text-align: center; border: 2px solid #e94560; }\n'
        '.cta-block h3 { margin-bottom: 15px; color: #1a1a2e; }\n'
        '.cta-block a { display: inline-block; background: linear-gradient(135deg,#e94560,#c44569); color: #fff; padding: 14px 35px; border-radius: 30px; text-decoration: none; font-weight: 700; margin-top: 10px; }\n'
        'footer { text-align: center; padding: 40px 20px; color: rgba(255,255,255,0.7); }\n'
        'footer a { color: #e94560; font-weight: 600; text-decoration: none; }\n'
        '</style>\n'
        '</head>\n'
        '<body>\n'
        '<div class="container">\n'
        '<header>\n'
        '<h1>Юридический дайджест</h1>\n'
        '<p>Aктуальные новости по <strong>семейному</strong> и <strong>трудовому</strong> праву РФ</p>\n'
        '<nav>\n'
        '<a href="' + SITE_URL + '">&larr; серко.рф</a>\n'
        '<a href="https://t.me/ConsulLexbot" target="_blank">@ConsulLexbot</a>\n'
        '</nav>\n'
        '</header>\n\n'
        + cards_html + '\n\n'
        '<div class="cta-block">\n'
        '<h3>Oстались вопросы по теме?</h3>\n'
        '<p>Юрист Серко И.И. ответит лично через Telegram-бота</p>\n'
        '<a href="https://t.me/ConsulLexbot" target="_blank" rel="noopener noreferrer">Написать боту @ConsulLexbot</a>\n'
        '<p style="margin-top:10px; font-size:13px; color:#888;">Ответ в течение суток &bull; Консультация от 2 000 руб. &bull; Работаю по всей России</p>\n'
        '</div>\n\n'
        '<footer>\n'
        '<p>&copy; Юридический дайджест | <a href="' + SITE_URL + '">серко.рф</a> | <a href="https://t.me/ConsulLexbot" target="_blank" rel="noopener noreferrer">@ConsulLexbot</a></p>\n'
        '</footer>\n'
        '</div>\n'
        '</body>\n'
        '</html>'
    )

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print("[OK] Сгенерирован: index.html")

def build_sitemap(posts):
    """Генерирует sitemap.xml"""

    urls = [
        '<url>\n'
        '    <loc>' + SITE_URL + BLOG_PATH + '/</loc>\n'
        '    <lastmod>' + datetime.now().strftime("%Y-%m-%d") + '</lastmod>\n'
        '    <changefreq>weekly</changefreq>\n'
        '    <priority>0.9</priority>\n'
        '  </url>'
    ]

    for p in posts:
        urls.append(
            '<url>\n'
            '    <loc>' + p["canonical"] + '</loc>\n'
            '    <lastmod>' + p["date"] + '</lastmod>\n'
            '    <changefreq>monthly</changefreq>\n'
            '    <priority>0.8</priority>\n'
            '  </url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + '\n'
        '</urlset>'
    )

    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

    print("[OK] Сгенерирован: sitemap.xml")

def build_robots():
    """Генерирует robots.txt"""
    txt = (
        'User-agent: *\n'
        'Allow: /\n'
        'Sitemap: ' + SITE_URL + BLOG_PATH + '/sitemap.xml'
    )

    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(txt)

    print("[OK] Сгенерирован: robots.txt")

# ==========================================
# ГЛАВНЫЙ ЗАПУСК
# ==========================================
if __name__ == "__main__":
    print("=" * 50)
    print("  СБОРКА БЛОГА")
    print("=" * 50)

    posts = build_posts()
    build_index(posts)
    build_sitemap(posts)
    build_robots()

    print("=" * 50)
    print("Готово! Постов: " + str(len(posts)))
    print("Теперь закоммитьте и запушьте:")
    print("  git add .")
    print("  git commit -m 'обновление блога'")
    print("  git push")
