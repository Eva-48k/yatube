from django.core.paginator import Paginator


amount = 10  # Количество постов на странице


def get_paginator(request, post_list):
    paginator = Paginator(post_list, amount)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
