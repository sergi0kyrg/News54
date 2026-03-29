from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, News, Source


def news_list(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    source_id = request.GET.get('source', '').strip()
    sort = request.GET.get('sort', 'new')

    qs = News.objects.select_related('category', 'source').all()

    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        )

    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    if source_id:
        qs = qs.filter(source_id=source_id)

    if sort == 'old':
        qs = qs.order_by('published_at')
    else:
        qs = qs.order_by('-published_at')

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'sources': Source.objects.filter(is_active=True),
        'query': query,
        'selected_category': category_slug,
        'selected_source': source_id,
        'sort': sort,
    }
    return render(request, 'news/news_list.html', context)


def news_detail(request, slug):
    item = get_object_or_404(News.objects.select_related('category', 'source'), slug=slug)
    return render(request, 'news/news_detail.html', {'item': item})
