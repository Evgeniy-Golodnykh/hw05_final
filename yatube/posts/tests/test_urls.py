from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post_author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(PostURLTests.post_author)
        self.status_code_url_names = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/follow/': HTTPStatus.OK,
            '/unexisting_name/': HTTPStatus.NOT_FOUND,
        }
        cache.clear()

    def test_post_url_from_guest_client(self):
        """Проверяем доступность страниц любому пользователю."""
        status_code_url_names = self.status_code_url_names
        status_code_url_names['/create/'] = HTTPStatus.FOUND
        status_code_url_names['/posts/1/edit/'] = HTTPStatus.FOUND
        status_code_url_names['/follow/'] = HTTPStatus.FOUND
        for address, status_code in status_code_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_post_url_from_authorized_client(self):
        """Проверяем доступность страниц авторизованному пользователю."""
        status_code_url_names = self.status_code_url_names
        status_code_url_names['/posts/1/edit/'] = HTTPStatus.FOUND
        for address, status_code in status_code_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_post_url_from_post_author_client(self):
        """Проверяем доступность страниц автору поста."""
        status_code_url_names = self.status_code_url_names
        for address, status_code in status_code_url_names.items():
            with self.subTest(address=address):
                response = self.post_author_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.post_author_client.get(address)
                self.assertTemplateUsed(response, template)
