from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Follow

User = get_user_model()


class PostsViewsFollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.create_user(username='author')
        cls.new_author = User.objects.create_user(username='new_author')
        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.author
        )
        cls.follow = Follow.objects.create(
            user_id=cls.user.id,
            author_id=cls.author.id
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_for_authorized(self):
        """
        Проверяем, что авторизованный пользователь может подписываться на
        других пользователей.
        """
        # Авторизованный пользователь подписывается на нового автора
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.new_author.username}))
        # Проверяем, что подписка создалась
        self.assertTrue(Follow.objects.filter(
                        user_id=self.user.id,
                        author_id=self.new_author.id).exists()
                        )

    def test_unfollow_for_authorized(self):
        """
        Проверяем, что авторизованный пользователь может удалять подписки.
        """
        # Авторизованный пользователь нажимает на кнопку "Отписаться"
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}))
        # Проверяем, что подписка удалилась
        self.assertFalse(Follow.objects.filter(
            user_id=self.user.id,
            author_id=self.author.id).exists()
        )

    def test_show_new_post_for_follower(self):
        """
        Проверяем, что новая запись пользователя появляется в ленте тех,
        кто на него подписан.
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        new_post = response.context['page_obj'][0]
        self.assertEqual(new_post, self.post)

    def test_show_new_post_for_not_follower(self):
        """
        Проверяем, что новая запись пользователя не появляется в ленте тех,
        кто на него не подписан.
        """
        not_follower = User.objects.create_user(username='not_follower')
        authorized_client = Client()
        authorized_client.force_login(not_follower)
        response = authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
