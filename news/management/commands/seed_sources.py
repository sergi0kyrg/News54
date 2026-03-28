from django.core.management.base import BaseCommand

from news.models import Source

DEFAULT_SOURCES = [
    {
        'name': 'NGS Новости',
        'base_url': 'https://ngs.ru/',
        'source_type': 'rss',
        'rss_url': 'https://ngs.ru/text/rss.xml',
        'is_active': True,
    },
    {
        'name': 'VN.ru',
        'base_url': 'https://vn.ru/',
        'source_type': 'rss',
        'rss_url': 'https://vn.ru/rss/',
        'is_active': True,
    },
    {
        'name': 'Om1 Новосибирск',
        'base_url': 'https://www.om1.ru/',
        'source_type': 'rss',
        'rss_url': 'https://www.om1.ru/rss/news/',
        'is_active': True,
    },
]


class Command(BaseCommand):
    help = 'Добавляет стартовые RSS-источники для News54'

    def handle(self, *args, **options):
        created = 0
        for item in DEFAULT_SOURCES:
            _, was_created = Source.objects.update_or_create(
                name=item['name'],
                defaults=item,
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Готово. Добавлено новых источников: {created}'))
