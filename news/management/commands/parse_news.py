from datetime import datetime
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from news.models import Category, News, Source

DEFAULT_CATEGORY_KEYWORDS = {
    'Политика': ['мэр', 'губернатор', 'правительство', 'администрация', 'депутат'],
    'Происшествия': ['дтп', 'пожар', 'авария', 'полиция', 'суд', 'чп'],
    'Экономика': ['бюджет', 'бизнес', 'предприятие', 'инвестиции', 'налог'],
    'Общество': ['школ', 'больниц', 'жител', 'социаль', 'город'],
    'Спорт': ['спорт', 'матч', 'хоккей', 'футбол', 'турнир'],
    'Культура': ['театр', 'музей', 'концерт', 'выставк', 'фестиваль'],
}


def detect_category(title: str, summary: str):
    text = f'{title} {summary}'.lower()
    for category_name, keywords in DEFAULT_CATEGORY_KEYWORDS.items():
        if any(word in text for word in keywords):
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={'slug': slugify(category_name)},
            )
            return category
    category, _ = Category.objects.get_or_create(name='Без категории', defaults={'slug': 'bez-kategorii'})
    return category


def extract_image_from_entry(entry) -> str:
    media = entry.get('media_content') or []
    if media and isinstance(media, list):
        url = media[0].get('url')
        if url:
            return url
    enclosures = entry.get('enclosures') or []
    if enclosures and isinstance(enclosures, list):
        url = enclosures[0].get('href')
        if url:
            return url
    summary = entry.get('summary', '')
    soup = BeautifulSoup(summary, 'html.parser')
    img = soup.find('img')
    return img['src'] if img and img.get('src') else ''


class Command(BaseCommand):
    help = 'Загрузка новостей из RSS/HTML источников'

    def handle(self, *args, **options):
        sources = Source.objects.filter(is_active=True)
        if not sources.exists():
            self.stdout.write(self.style.WARNING('Нет активных источников.'))
            return

        created_count = 0
        for source in sources:
            try:
                if source.source_type == 'rss':
                    created_count += self.parse_rss(source)
                else:
                    created_count += self.parse_html(source)
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'{source.name}: ошибка {exc}'))

        self.stdout.write(self.style.SUCCESS(f'Готово. Добавлено новостей: {created_count}'))

    def parse_rss(self, source: Source) -> int:
        feed_url = source.rss_url or source.base_url
        feed = feedparser.parse(feed_url)
        added = 0

        for entry in feed.entries:
            link = entry.get('link')
            if not link or News.objects.filter(original_url=link).exists():
                continue

            title = (entry.get('title') or '').strip()[:500]
            summary = BeautifulSoup(entry.get('summary', ''), 'html.parser').get_text(' ', strip=True)
            published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
            if published_parsed:
                published_at = timezone.make_aware(datetime(*published_parsed[:6]), timezone.get_current_timezone())
            else:
                published_at = timezone.now()

            category = detect_category(title, summary)
            slug = slugify(title)[:500] or f'news-{int(timezone.now().timestamp())}'
            slug = self.make_unique_slug(slug)
            image_url = extract_image_from_entry(entry)

            News.objects.create(
                title=title,
                slug=slug,
                summary=summary,
                content=summary,
                original_url=link,
                image_url=image_url,
                published_at=published_at,
                source=source,
                category=category,
            )
            added += 1
        return added

    def parse_html(self, source: Source) -> int:
        response = requests.get(source.base_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select(source.item_selector)
        added = 0

        for item in items:
            title_el = item.select_one(source.title_selector) if source.title_selector else None
            link_el = item.select_one(source.link_selector) if source.link_selector else None
            summary_el = item.select_one(source.summary_selector) if source.summary_selector else None
            image_el = item.find('img')

            title = title_el.get_text(' ', strip=True)[:500] if title_el else ''
            href = link_el.get('href') if link_el else None
            link = urljoin(source.base_url, href) if href else None
            summary = summary_el.get_text(' ', strip=True) if summary_el else ''
            image_url = urljoin(source.base_url, image_el.get('src')) if image_el and image_el.get('src') else ''

            if not title or not link or News.objects.filter(original_url=link).exists():
                continue

            category = detect_category(title, summary)
            slug = self.make_unique_slug(slugify(title)[:500] or f'news-{int(timezone.now().timestamp())}')
            News.objects.create(
                title=title,
                slug=slug,
                summary=summary,
                content=summary,
                original_url=link,
                image_url=image_url,
                published_at=timezone.now(),
                source=source,
                category=category,
            )
            added += 1
        return added

    def make_unique_slug(self, base_slug: str) -> str:
        slug = base_slug
        counter = 1
        while News.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1
        return slug
