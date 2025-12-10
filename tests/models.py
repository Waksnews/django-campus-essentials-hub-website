# tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Badge
from lost_found.models import LostItem
from tutoring.models import Tutor
from datetime import date


class UserModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@university.ac.ke',
            password='testpass123',
            student_id='SC001',
            university='Test University'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'testuser@university.ac.ke')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertEqual(self.user.student_id, 'SC001')

    def test_user_str_representation(self):
        self.assertEqual(str(self.user), 'testuser (testuser@university.ac.ke)')


class LostItemModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@university.ac.ke',
            password='testpass123'
        )
        self.item = LostItem.objects.create(
            user=self.user,
            title='Test Laptop',
            description='MacBook Pro 16"',
            category='electronics',
            status='lost',
            location_lost='Library',
            date_lost=date.today(),
            contact_info='test@example.com'
        )

    def test_item_creation(self):
        self.assertEqual(self.item.title, 'Test Laptop')
        self.assertEqual(self.item.status, 'lost')
        self.assertEqual(self.item.category, 'electronics')
        self.assertFalse(self.item.is_resolved)

    def test_item_str_representation(self):
        self.assertEqual(str(self.item), 'Test Laptop - Lost')


class TutorModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tutoruser',
            email='tutor@university.ac.ke',
            password='testpass123'
        )
        self.tutor = Tutor.objects.create(
            user=self.user,
            subjects='Programming,Mathematics',
            primary_subject='programming',
            year_of_study='senior',
            hourly_rate=500.00,
            bio='Expert tutor',
            qualifications='BSc Computer Science',
            availability='Weekends'
        )

    def test_tutor_creation(self):
        self.assertEqual(self.tutor.primary_subject, 'programming')
        self.assertEqual(self.tutor.hourly_rate, 500.00)
        self.assertTrue(self.tutor.is_available)

    def test_tutor_str_representation(self):
        self.assertEqual(str(self.tutor), 'tutoruser - Programming Tutor')