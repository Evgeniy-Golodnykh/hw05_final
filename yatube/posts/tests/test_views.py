import math
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=(
                b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
            ),
            content_type='image/gif',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовая группа в которой будет один пост',
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new-group',
            description='Тестовая группа в которой не будет постов',
        )
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPageTests.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'auth'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': 1}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': 1}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_pages_has_one_post(self):
        """Шаблоны страниц отображают правильное количество постов"""
        pages_reverse_name = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        )
        for reverse_name in pages_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_new_group_posts_has_no_post(self):
        """Шаблон страницы новой группы не имеет постов"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'new-group'})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_posts_pages_show_correct_context(self):
        """Шаблоны страниц с постами сформированы с правильным контекстом."""
        pages_reverse_name = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
            reverse('posts:post_detail', kwargs={'post_id': 1}),
        )
        for reverse_name in pages_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if 'post' in response.context:
                    first_object = response.context['post']
                else:
                    first_object = response.context['page_obj'][0]
                post_text = first_object.text
                post_image = first_object.image
                self.assertEqual(post_text, 'Тестовый пост')
                self.assertEqual(post_image, 'posts/small.gif')

    def test_posts_forms_show_correct_context(self):
        """Шаблоны страниц с формами сформированы с правильным контекстом."""
        pages_reverse_name = (
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            reverse('posts:post_create'),
        )
        for reverse_name in pages_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                    'image': forms.fields.ImageField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)

    def test_posts_cache(self):
        '''Кеширование главной страницы работает корректно'''
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response_del = self.authorized_client.get(reverse('posts:index'))
        cache.clear()
        response_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_del.content)
        self.assertNotEqual(response.content, response_clear.content)

    def test_posts_follow_pages_show_correct_context(self):
        """Шаблоны страниц подписчика и неподписчика работают корректно"""
        follower = User.objects.create_user(username='follower')
        not_follower = User.objects.create_user(username='not_follower')
        self.follower = Client()
        self.not_follower = Client()
        self.follower.force_login(follower)
        self.not_follower.force_login(not_follower)
        self.follower.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'})
        )
        response_flwg = self.follower.get(reverse('posts:follow_index'))
        response_unflwg = self.not_follower.get(reverse('posts:follow_index'))
        post_text_flwg = response_flwg.context['page_obj'][0].text
        posts_count_flwg = len(response_flwg.context['page_obj'])
        posts_count_unflwg = len(response_unflwg.context['page_obj'])
        self.assertEqual(post_text_flwg, 'Тестовый пост')
        self.assertEqual(posts_count_flwg, 1)
        self.assertEqual(posts_count_unflwg, 0)

    def test_user_follow_unfollow(self):
        """Пользователь может подписываться и отписываться на/от авторов"""
        follower = User.objects.create_user(username='follower')
        self.follower = Client()
        self.follower.force_login(follower)
        follow_count = Follow.objects.count()
        self.follower.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'})
        )
        follow_count_subscribe = Follow.objects.count()
        self.follower.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'auth'})
        )
        follow_count_unsubscribe = Follow.objects.count()
        self.assertEqual(follow_count_subscribe, follow_count + 1)
        self.assertEqual(follow_count_unsubscribe, follow_count)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user = User.objects.create_user(username='auth')
        cls.TEST_POSTS_COUNT = 11
        cls.paginator_reverse_name = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        )
        cls.objs = [
            Post.objects.create(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
            )
            for _ in range(cls.TEST_POSTS_COUNT)
        ]
        Post.objects.bulk_create(objs=cls.objs, ignore_conflicts=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        cache.clear()

    def test_first_page_contains_correct_records(self):
        """Первая страница отображает корректное количество постов"""
        paginator_reverse_name = PaginatorViewsTest.paginator_reverse_name
        for reverse_name in paginator_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE,
                )

    def test_last_page_contains_correct_records(self):
        """Последняя страница отображает корректное количество постов"""
        paginator_reverse_name = PaginatorViewsTest.paginator_reverse_name
        last_page_number = math.ceil(
            PaginatorViewsTest.TEST_POSTS_COUNT
            / settings.POSTS_PER_PAGE
        )
        last_page_posts_count = (
            PaginatorViewsTest.TEST_POSTS_COUNT
            % settings.POSTS_PER_PAGE
            or settings.POSTS_PER_PAGE
        )
        for reverse_name in paginator_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name + f'?page={last_page_number}'
                )
                self.assertEqual(
                    len(response.context['page_obj']), last_page_posts_count
                )
