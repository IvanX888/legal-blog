---
layout: default
title: Юридический дайджест
---

# ⚖️ Юридический дайджест

Автоматическая подборка новостей по **семейному** и **трудовому** праву РФ.

---

## 📋 Последние записи

{% for post in site.posts %}
### [{{ post.title }}]({{ post.url | relative_url }})

📅 {{ post.date | date: "%d.%m.%Y" }} | 🏷️ {{ post.categories | join: ", " }}

{{ post.excerpt | strip_html | truncate: 200 }}

---

{% endfor %}

{% if site.posts.size == 0 %}
*Пока записей нет. Бот собирает новости каждый день в 9:00.*
{% endif %}
