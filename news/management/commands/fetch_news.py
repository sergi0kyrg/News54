import feedparser
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from news.models import Source, News, Category

REGION_KEYWORDS = [
    "новосибирск",
    "новосибирская область",
    "новосибирской области",
    "новосибирец",
    "новосибирцы",
    "бердск",
    "искитим",
    "обь",
    "кольцово",
    "академгородок",
    "краснообск",
    "татарск",
    "карасук",
    "купино",
    "барабинск",
    "чулым",
    "тогучин",
    "мошково",
    "ордынское",
    "коченево",
    "куйбышев",
    "обское море",
]

CATEGORY_KEYWORDS = {
    "Политика": [
        "губернатор", "мэр", "правительство", "закон",
        "администрация", "депутат", "власть", "министр"
    ],
    "Общество": [
        "школ", "жител", "больниц", "поликлиник",
        "дорог", "транспорт", "автобус", "метро",
        "детский сад", "образование", "медицина",
        "жкх", "ремонт", "благоустройство"
    ],
    "Спорт": [
        "спорт", "матч", "хоккей", "футбол",
        "турнир", "спортсмен", "чемпионат", "команда"
    ],
    "Культура": [
        "театр", "музей", "фестиваль", "концерт",
        "выставк", "культура", "спектакль", "библиотек",
        "галере", "искусств"
    ],
    "Экономика": [
        "бюджет", "завод", "бизнес", "предприятие",
        "экономик", "инвестиц", "рынок", "производство",
        "строительств", "зарплат", "налог"
    ],
    "Происшествия": [
        "дтп", "пожар", "суд", "авария",
        "полиция", "прокуратура", "преступлен", "чп",
        "мчс", "столкновен", "задержан", "ранен"
    ],
}

def build_entry_text(entry) -> str:
    parts = []

    title = entry.get("title", "")
    summary = entry.get("summary", "")
    description = entry.get("description", "")

    if title:
        parts.append(title)
    if summary:
        parts.append(summary)
    if description:
        parts.append(description)

    if entry.get("tags"):
        for tag in entry.tags:
            term = tag.get("term", "")
            if term:
                parts.append(term)

    return " ".join(parts).lower()

def is_regional_news(entry) -> bool:
    text = build_entry_text(entry)
    return any(keyword in text for keyword in REGION_KEYWORDS)

def detect_category(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()

    for category_name, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category_name

    return "Общество"

def get_unique_news_slug(title: str) -> str:
    base_slug = slugify(title)[:200] or "news"
    slug = base_slug
    counter = 1

    while News.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug

def get_or_create_category(category_name: str) -> Category:
    category = Category.objects.filter(name=category_name).first()
    if category:
        return category

    base_slug = slugify(category_name) or "category"
    slug = base_slug
    counter = 1

    while Category.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return Category.objects.create(
        name=category_name,
        slug=slug
    )

def extract_image_url(entry) -> str:
    if "media_content" in entry and entry.media_content:
        media_item = entry.media_content[0]
        url = media_item.get("url", "")
        if url:
            return url

    if "media_thumbnail" in entry and entry.media_thumbnail:
        thumb_item = entry.media_thumbnail[0]
        url = thumb_item.get("url", "")
        if url:
            return url

    if "enclosures" in entry and entry.enclosures:
        enclosure = entry.enclosures[0]
        url = enclosure.get("href", "") or enclosure.get("url", "")
        if url:
            return url

    if "links" in entry:
        for link_obj in entry.links:
            link_type = link_obj.get("type", "")
            if link_type.startswith("image/"):
                url = link_obj.get("href", "")
                if url:
                    return url

    return ""


class Command(BaseCommand):
    help = "Загружает новости из RSS и сохраняет только публикации по Новосибирску и Новосибирской области"

    def handle(self, *args, **kwargs):
        sources = Source.objects.filter(is_active=True)

        if not sources.exists():
            self.stdout.write(self.style.WARNING("Нет активных источников"))
            return

        added_count = 0
        skipped_count = 0

        for source in sources:
            self.stdout.write(f"Источник: {source.name}")

            if not source.rss_url:
                self.stdout.write(
                    self.style.WARNING(f"У источника '{source.name}' не указан RSS URL")
                )
                continue

            feed = feedparser.parse(source.rss_url)

            if not feed.entries:
                self.stdout.write(
                    self.style.WARNING(f"Пустая RSS-лента: {source.name}")
                )
                continue

            for entry in feed.entries:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                link = entry.get("link", "").strip()

                if not title or not link:
                    skipped_count += 1
                    continue

                if News.objects.filter(original_url=link).exists():
                    skipped_count += 1
                    continue

                if not is_regional_news(entry):
                    skipped_count += 1
                    continue

                category_name = detect_category(title, summary)
                category = get_or_create_category(category_name)

                slug = get_unique_news_slug(title)
                image_url = extract_image_url(entry)

                News.objects.create(
                    title=title,
                    summary=summary,
                    content=summary,
                    original_url=link,
                    image_url=image_url,
                    source=source,
                    category=category,
                    slug=slug,
                    published_at=timezone.now()
                )

                added_count += 1
                self.stdout.write(self.style.SUCCESS(f"Добавлена: {title}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Добавлено: {added_count}, пропущено: {skipped_count}"
            )
        )



