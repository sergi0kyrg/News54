from django.contrib import admin
from .models import Category, Favorite, News, Source


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'base_url', 'is_active')
    list_filter = ('source_type', 'is_active')
    search_fields = ('name', 'base_url', 'rss_url')


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'category', 'published_at')
    list_filter = ('source', 'category', 'published_at')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('source', 'category', 'author')
    ordering = ('-published_at',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'news', 'created_at')
    search_fields = ('user__username', 'news__title')
