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
            with open(os.path.join(POSTS_DIR, fname
