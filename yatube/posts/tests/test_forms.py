import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment
from posts.forms import PostForm, CommentForm

User = get_user_model()

# Создаем временную папку для медиа-файлов
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='тестовый заголовок',
            slug='test-slug',
            description='тестовое описание'
        )
        cls.new_group = Group.objects.create(
            title='новый заголовок',
            slug='new-slug',
            description='новое описание'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            group=cls.group,
            author=cls.author,
        )
        cls.form = PostForm()
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='тестовый комментарий'
        )
        cls.comment_form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_create_post(self):
        """
        Проверяем, что при отправке валидной формы со страницы создания поста
        создается запись в БД.
        """
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'тестовый текст',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='тестовый текст',
                group=self.group,
                image='posts/small.gif',
            ).exists()
        )

    def test_create_post_for_anonymous(self):
        """
        Проверяем, что неавторизованный пользователь не может создать пост
        """
        post_count = Post.objects.count()
        form_data = {
            'text': 'тестовый текст',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(response, reverse('login')
                             + '?next=' + reverse('posts:post_create'))
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post(self):
        """
        Проверяем, что при отправке валидной формы со страницы редактирования
        поста происходит изменение в БД.
        """
        post_count = Post.objects.count()

        form_data = {
            'text': 'отредактированный текст',
            'group': self.new_group.id,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.post.refresh_from_db()
        self.assertEqual(Post.objects.count(), post_count)
        # Проверка, если изменили текст поста
        self.assertEqual(self.post.text, form_data['text'])
        # Проверка, если изменили группу поста
        self.assertEqual(self.post.group_id, form_data['group'])

    def test_edit_post_from_anonymous(self):
        """
        Проверяем, что неавторизованный пользователь не может изменить пост.
        """
        post_count = Post.objects.count()
        form_data = {
            'text': 'отредактированный текст',
            'group': self.new_group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.post.refresh_from_db()
        # Проверяем, что не изменился текст поста
        self.assertNotEqual(self.post.text, form_data['text'])
        # Проверяем, что не изменилась группа поста
        self.assertNotEqual(self.post.group_id, form_data['group'])

    def test_edit_post_no_author(self):
        """
        Проверяем, что авторизованный пользователь, не являющийся
        автором поста, не может изменить пост.
        """
        post_count = Post.objects.count()
        form_data = {
            'text': 'отредактированный текст',
            'group': self.new_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.post.refresh_from_db()
        # Проверяем, что не изменился текст поста
        self.assertNotEqual(self.post.text, form_data['text'])
        # Проверяем, что не изменилась группа поста
        self.assertNotEqual(self.post.group_id, form_data['group'])

    def test_create_comment(self):
        """
        Проверяем, что при отправке валидной формы создаётся комментарий в БД.
        """
        comment_count = Comment.objects.count()
        form_data = {'text': 'тестовый комментарий'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='тестовый комментарий',
                post=self.post.id
            ).exists()
        )

    def test_edit_post_from_anonymous(self):
        """
        Проверяем, что неавторизованный пользователь не может
        создать комментарий.
        """
        comment_count = Comment.objects.count()
        form_data = {'text': 'тестовый комментарий'}
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count)
