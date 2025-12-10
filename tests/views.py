# tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model


class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('home')

    def test_home_view_status_code(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

    def test_home_view_template(self):
        response = self.client.get(self.home_url)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_home_view_context(self):
        response = self.client.get(self.home_url)
        self.assertIn('stats', response.context)


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@university.ac.ke',
            'student_id': 'SC001',
            'university': 'Test University',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, 302)  # Redirect after registration

        # Check if user was created
        user = get_user_model().objects.filter(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@university.ac.ke')

    def test_user_login(self):
        # Create user first
        get_user_model().objects.create_user(
            username='testuser',
            email='test@university.ac.ke',
            password='TestPass123!'
        )

        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login

        # Check if user is authenticated
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)


class LostFoundViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@university.ac.ke',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.list_url = reverse('lost_found:list')

    def test_lost_found_list_view(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lost_found/list.html')

    def test_lost_item_creation(self):
        create_url = reverse('lost_found:create_lost')
        response = self.client.post(create_url, {
            'title': 'Lost Phone',
            'description': 'iPhone 13',
            'category': 'electronics',
            'location_lost': 'Cafeteria',
            'date_lost': '2024-01-15',
            'contact_info': 'test@example.com'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation