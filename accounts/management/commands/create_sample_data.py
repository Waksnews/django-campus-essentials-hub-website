# accounts/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Badge
from lost_found.models import LostItem
from tutoring.models import Tutor
from jobs.models import Job
from resources.models import Resource
from services.models import Service
import random
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Creates sample data for testing'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Create sample users
        users = []
        for i in range(1, 11):
            user, created = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'email': f'student{i}@university.ac.ke',
                    'student_id': f'SC{i:03d}',
                    'university': 'Sample University',
                    'course': random.choice(['Computer Science', 'Engineering', 'Business', 'Medicine']),
                    'year_of_study': random.randint(1, 4),
                    'is_verified': True,
                }
            )
            user.set_password('password123')
            user.save()
            users.append(user)
            self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))

        # Create lost items
        categories = ['electronics', 'documents', 'clothing', 'books', 'other']
        statuses = ['lost', 'found', 'returned']

        for i in range(20):
            item = LostItem.objects.create(
                user=random.choice(users),
                title=f'Lost Item {i + 1}',
                description=f'Description for lost item {i + 1}',
                category=random.choice(categories),
                status=random.choice(statuses),
                location_lost=f'Location {random.randint(1, 10)}',
                date_lost=date.today() - timedelta(days=random.randint(1, 30)),
                contact_info=f'Contact {i + 1}',
                is_resolved=random.choice([True, False])
            )

        self.stdout.write(self.style.SUCCESS('Created sample data successfully!'))