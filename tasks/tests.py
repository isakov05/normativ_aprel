from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tasks.models import Tasks
from tasks.serializers import TasksSerializer


class TaskUnitTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='strongpass123')
        self.other = User.objects.create_user(username='other', password='strongpass123')

    def test_create_task(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('tasks-list')
        data = {'title': 'First task', 'content': 'This is a valid content'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'First task')
        self.assertEqual(Tasks.objects.count(), 1)
        self.assertEqual(Tasks.objects.first().author, self.owner)

    def test_serializer_valid(self):
        serializer = TasksSerializer(data={'title': 'Valid', 'content': 'Long enough content'})
        self.assertTrue(serializer.is_valid())

    def test_serializer_empty_title(self):
        serializer = TasksSerializer(data={'title': '   ', 'content': 'Long enough content'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_serializer_short_content(self):
        serializer = TasksSerializer(data={'title': 'Valid', 'content': 'short'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)

    def test_author_is_read_only(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('tasks-list')
        data = {'title': 'Spoof', 'content': 'Trying to set another author', 'author': self.other.id}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tasks.objects.first().author, self.owner)

    def test_permission_owner_can_update(self):
        task = Tasks.objects.create(title='Mine', content='Owner content here', author=self.owner)
        self.client.force_authenticate(user=self.owner)
        url = reverse('tasks-detail', args=[task.id])

        response = self.client.patch(url, {'title': 'Updated'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated')

    def test_permission_non_owner_cannot_update(self):
        task = Tasks.objects.create(title='Mine', content='Owner content here', author=self.owner)
        self.client.force_authenticate(user=self.other)
        url = reverse('tasks-detail', args=[task.id])

        response = self.client.patch(url, {'title': 'Hacked'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create(self):
        url = reverse('tasks-list')
        response = self.client.post(url, {'title': 'x', 'content': 'long enough content'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskIntegrationTests(APITestCase):
    def test_register_login_token_and_crud_flow(self):
        register_response = self.client.post(
            '/api/register/',
            {'username': 'integration', 'password': 'strongpass123', 'confirm_password': 'strongpass123'},
            format='json',
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='integration').exists())

        login_response = self.client.post(
            '/api/login/',
            {'username': 'integration', 'password': 'strongpass123'},
            format='json',
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token_response = self.client.post(
            '/api/token',
            {'username': 'integration', 'password': 'strongpass123'},
            format='json',
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        access = token_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        create_response = self.client.post(
            reverse('tasks-list'),
            {'title': 'Integration task', 'content': 'Created with a JWT token'},
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        task_id = create_response.data['id']

        list_response = self.client.get(reverse('tasks-list'))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['count'], 1)

        detail_response = self.client.get(reverse('tasks-detail', args=[task_id]))
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['title'], 'Integration task')

        update_response = self.client.put(
            reverse('tasks-detail', args=[task_id]),
            {'title': 'Updated task', 'content': 'Updated with a JWT token'},
            format='json',
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['title'], 'Updated task')


class TaskQueryOptimizationTests(APITestCase):
    def setUp(self):
        cache.clear()
        for i in range(5):
            user = User.objects.create_user(username=f'user{i}', password='strongpass123')
            Tasks.objects.create(title=f'Task {i}', content='Some long enough content', author=user)

    def test_list_uses_constant_number_of_queries(self):
        url = reverse('tasks-list')
        with self.assertNumQueries(2):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TaskThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_anonymous_is_throttled_after_limit(self):
        url = reverse('tasks-list')

        for _ in range(10):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class TaskCacheTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='cacheuser', password='strongpass123')

    def test_list_response_is_cached(self):
        Tasks.objects.create(title='First', content='Long enough content', author=self.user)
        url = reverse('tasks-list')

        first = self.client.get(url)
        self.assertEqual(first.data['count'], 1)

        Tasks.objects.create(title='Second', content='Long enough content', author=self.user)
        second = self.client.get(url)
        self.assertEqual(second.data['count'], 1)

    def test_cache_invalidated_after_create(self):
        url = reverse('tasks-list')

        self.client.get(url)

        self.client.force_authenticate(user=self.user)
        create = self.client.post(
            url,
            {'title': 'Fresh', 'content': 'Long enough content'},
            format='json',
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)

        after = self.client.get(url)
        self.assertEqual(after.data['count'], 1)
