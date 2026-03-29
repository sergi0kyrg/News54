from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=120, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Source(models.Model):
    SOURCE_TYPES = (
        ('rss', 'RSS'),
        ('html', 'HTML'),
    )

    name = models.CharField('Источник', max_length=200, unique=True)
    base_url = models.URLField('Сайт')
    source_type = models.CharField('Тип', max_length=10, choices=SOURCE_TYPES, default='rss')
    rss_url = models.URLField('RSS URL', blank=True)
    is_active = models.BooleanField('Активен', default=True)

    # Селекторы для HTML-парсинга, если RSS нет
    item_selector = models.CharField(max_length=255, blank=True)
    title_selector = models.CharField(max_length=255, blank=True)
    link_selector = models.CharField(max_length=255, blank=True)
    summary_selector = models.CharField(max_length=255, blank=True)
    date_selector = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Источник'
        verbose_name_plural = 'Источники'
        ordering = ['name']

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField('Заголовок', max_length=500)
    slug = models.SlugField('Slug', max_length=520, unique=True)
    summary = models.TextField('Краткое описание', blank=True)
    content = models.TextField('Текст', blank=True)
    original_url = models.URLField('Ссылка на оригинал', unique=True)
    image_url = models.URLField('Изображение', blank=True)
    published_at = models.DateTimeField('Дата публикации')
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        related_name='news_items',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    source = models.ForeignKey(Source, verbose_name='Источник', related_name='news_items', on_delete=models.CASCADE)
    author = models.ForeignKey(
        User,
        verbose_name='Добавил вручную',
        related_name='manual_news',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news_detail', kwargs={'slug': self.slug})


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'news')

    def __str__(self):
        return f'{self.user.username} -> {self.news.title}'
