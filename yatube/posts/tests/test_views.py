import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, Comment

User = get_user_model()

# Создаем временную папку для медиа-файлов
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsViewsPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='тестовый заголовок',
            slug='test-slug',
            description='тестовое описание'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            group=cls.group,
            author=cls.author,
        )
        cache.clear()

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_view_uses_correct_template(self):
        """Проверяем, что view-классы используют ожидаемые HTML-шаблоны"""
        templates_view_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): (
                        'posts/profile.html'),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}): (
                        'posts/post_detail.html'),
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}): (
                        'posts/post_create.html')
        }
        for reverse_name, template in templates_view_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PostsViewsPaginatorTests(TestCase):
    """Проверяем, что paginator работает корректно"""
    def setUp(self):
        self.user = User.objects.create_user(username='Ivanov')
        self.group = Group.objects.create(
            title='тестовый заголовок',
            slug='test-slug',
            description='тестовое описание'
        )
        # Создаём 15 тестовых постов, из которых:
        # 13 постов имеют группу, 2 поста не имеют группы
        self.post_on_page = 10  # Количество постов на странице
        post_count = 15  # Общее количество постов
        post_count_with_group = 13  # Количество постов, имеющих группу
        new_posts = []
        for i in range(1, post_count + 1):
            if i <= post_count - post_count_with_group:
                group = None
            else:
                group = self.group
            new_posts.append(Post(
                text=f'тестовый текст № {i}',
                group=group,
                author=self.user,
            ))
        Post.objects.bulk_create(new_posts)
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Страницы, которые используют paginator
        self.paginator_views = {
            reverse('posts:index'): post_count,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): post_count_with_group,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): post_count,
        }

    def test_first_page_contains_ten_records(self):
        # Проверяем, что количество постов на первой странице не превышает 10
        for reverse_name, count in self.paginator_views.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), self.post_on_page)

    def test_second_page_contains_five_records(self):
        # Проверяем количество постов на второй странице
        for reverse_name, count in self.paginator_views.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    count - self.post_on_page)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsContextTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.no_author = User.objects.create_user(username='no_author')
        cls.group = Group.objects.create(
            title='тестовый заголовок',
            slug='test-slug',
            description='тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            group=cls.group,
            author=cls.author,
            image=cls.uploaded
        )
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.guest_client = Client()

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.image, self.post.image)

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.group, self.group)
        self.assertEqual(first_post.image, self.post.image)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.author.username}))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.author, self.author)
        self.assertEqual(first_post.image, self.post.image)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        one_post = response.context['post']
        self.assertEqual(one_post.id, self.post.id)
        self.assertEqual(one_post.image, self.post.image)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PostsViewsCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group_with_post = Group.objects.create(
            title='группа с постом',
            slug='test-slug-1',
            description='описание группы с постом'
        )
        cls.group_without_post = Group.objects.create(
            title='группа без поста',
            slug='test-slug-2',
            description='описание группы без поста'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            group=cls.group_with_post,
            author=cls.author
        )
        cache.clear()

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_show_new_post(self):
        """Проверяем, что новый пост появляется на нужных страницах."""
        # Страницы, на которых должен появиться новый пост
        tests_urls = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group_with_post.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author.username}),
        ]
        for url in tests_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                new_post = response.context['page_obj'][0]
                self.assertEqual(new_post, self.post)

    def test_new_post_in_correct_group(self):
        """Проверяем, что новый пост не попал в группу,
        для которой он не предназначен"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_without_post.slug}))
        if len(response.context['page_obj']) > 0:
            new_post = response.context['page_obj'][0]
            self.assertNotEqual(new_post.group, self.group_with_post)


class PostsViewsCommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.author
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='тестовый комментарий'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_show_new_comment(self):
        """Проверяем, что комментарий появляется на странице поста."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        new_comment = response.context['comments'][0]
        self.assertEqual(new_comment, self.comment)

    def test_create_comment_from_anonymous(self):
        """
        Проверяем, что неавторизованный пользователь не может
        создать комментарий.
        """
        comment_count = Comment.objects.count()
        form_data = {'text': 'новый тестовый комментарий'}
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertFalse(Comment.objects.filter(
            text='новый тестовый комментарий',
            post=self.post.id
        ).exists()
        )

    def test_create_comment_for_authorizedP(self):
        """
        Проверяем, что при отправке валидной формы авторизованным
        пользователем создаётся комментарий в БД.
        """
        comment_count = Comment.objects.count()
        form_data = {'text': 'новый тестовый комментарий'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='новый тестовый комментарий',
                post=self.post.id
            ).exists()
        )


class PostsViewsCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.author
        )

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_caсhes_for_index(self):
        """Проверяем, работу кэша на главной странице."""
        first_response = self.authorized_client_author.get(
            reverse('posts:index')).content
        self.post.delete()
        second_response = self.authorized_client_author.get(
            reverse('posts:index')).content
        self.assertEqual(first_response, second_response)
        cache.clear()
        new_response = self.authorized_client_author.get(
            reverse('posts:index')).content
        self.assertNotEqual(first_response, new_response)
