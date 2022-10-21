from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.utils import get_paginator
from django.views.decorators.cache import cache_page


from .models import User, Post, Group, Follow
from .forms import PostForm, CommentForm


@cache_page(20)
# View-функция для главной страницы:
def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': get_paginator(request, post_list)
    }
    return render(request, 'posts/index.html', context)


# View-функция для страницы сообщества:
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': get_paginator(request, post_list)
    }
    return render(request, 'posts/group_list.html', context)


# View-функция для профайла пользователя:
def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    post_list = user_profile.posts.all()
    # Cчётчик для вывода общего количества постов пользователя:
    post_count = user_profile.posts.count()

    # Проверяем, подписан ли текущий пользователь на автора
    user = request.user
    following = Follow.objects.filter(
        user_id=user.id,
        author_id=user_profile.id
    ).exists()

    context = {
        'user_profile': user_profile,
        'page_obj': get_paginator(request, post_list),
        'post_count': post_count,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


# View-функция для отдельного поста:
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    #  Cчётчик для вывода общего количества постов пользователя:
    post_count = Post.objects.filter(author_id=post.author_id).count()
    form = CommentForm()
    comment = post.comments.all()
    context = {
        'post': post,
        'post_count': post_count,
        'form': form,
        'comments': comment
    }
    return render(request, 'posts/post_detail.html', context)


# View-функция для страницы создания постов:
@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,  # Параметр для работы с файлами
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/post_create.html', {'form': form})


# View-функция для страницы редактирования постов:
@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,  # Параметр для работы с файлами
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)

    context = {
        'form': form,
        'post': post,
        'is_edit': True
    }

    return render(request, 'posts/post_create.html', context)


# View-функция для комментирования постов:
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


# View-функция для страницы с подписками
@login_required
def follow_index(request):
    user = request.user
    author_list = Follow.objects.filter(
        user_id=user.id).values_list('author_id')
    post_list = Post.objects.filter(author_id__in=author_list)
    context = {
        'page_obj': get_paginator(request, post_list)
    }
    return render(request, 'posts/follow.html', context)


# View-функция для подписки на автора
@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user and not Follow.objects.filter(
        user_id=user.id,
        author_id=author.id
    ).exists():
        Follow.objects.create(
            user_id=user.id,
            author_id=author.id
        )
    return redirect('posts:profile', username=username)


# View-функция для отписки
@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    following = Follow.objects.get(
        user_id=user.id,
        author_id=author.id
    )
    if following is not None:
        following.delete()
    return redirect('posts:profile', username=username)
