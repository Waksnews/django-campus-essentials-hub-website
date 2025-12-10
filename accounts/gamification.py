# accounts/gamification.py
from django.db.models import F
from .models import Badge
from datetime import datetime, timedelta


class GamificationEngine:
    def __init__(self, user):
        self.user = user

    def award_points(self, action_type, points):
        """Award points for user actions"""
        point_values = {
            'upload_resource': 20,
            'post_job': 15,
            'apply_job': 10,
            'book_tutor': 10,
            'complete_session': 25,
            'report_lost': 10,
            'report_found': 15,
            'return_item': 30,
            'write_review': 5,
            'verify_email': 50,
            'complete_profile': 20,
        }

        points_to_award = point_values.get(action_type, points)
        self.user.points = F('points') + points_to_award
        self.user.save(update_fields=['points'])
        self.user.refresh_from_db()

        # Check for badge achievements
        self.check_badges()

        return points_to_award

    def check_badges(self):
        """Check and award badges based on user activity"""
        badges_to_award = []

        # Top Tutor Badge
        if not self.user.badges.filter(badge_type='tutor').exists():
            from tutoring.models import Tutor
            tutor_profile = Tutor.objects.filter(user=self.user).first()
            if tutor_profile and tutor_profile.rating >= 4.5:
                badges_to_award.append('tutor')

        # Helpful Hero Badge
        if not self.user.badges.filter(badge_type='helper').exists():
            from resources.models import Resource
            resources_count = Resource.objects.filter(user=self.user).count()
            if resources_count >= 10:
                badges_to_award.append('helper')

        # Finder Star Badge
        if not self.user.badges.filter(badge_type='finder').exists():
            from lost_found.models import FoundItem
            found_items = FoundItem.objects.filter(user=self.user, is_claimed=True).count()
            if found_items >= 5:
                badges_to_award.append('finder')

        # Active User Badge
        if not self.user.badges.filter(badge_type='active').exists():
            # Check if user has been active in multiple features
            from datetime import date, timedelta
            thirty_days_ago = date.today() - timedelta(days=30)

            activity_count = 0
            # Check lost/found activity
            from lost_found.models import LostItem
            activity_count += LostItem.objects.filter(
                user=self.user,
                created_at__date__gte=thirty_days_ago
            ).count()

            # Check job activity
            from jobs.models import Job
            activity_count += Job.objects.filter(
                user=self.user,
                created_at__date__gte=thirty_days_ago
            ).count()

            if activity_count >= 15:
                badges_to_award.append('active')

        # Subject Expert Badge
        if not self.user.badges.filter(badge_type='expert').exists():
            from tutoring.models import Tutor
            tutor_profile = Tutor.objects.filter(user=self.user).first()
            if tutor_profile and tutor_profile.total_sessions >= 20:
                badges_to_award.append('expert')

        # Award badges
        for badge_type in badges_to_award:
            self.award_badge(badge_type)

    def award_badge(self, badge_type):
        """Award a specific badge to the user"""
        badge_descriptions = {
            'tutor': {
                'title': 'Top Tutor',
                'description': 'Awarded for maintaining a 4.5+ rating as a tutor',
                'icon': 'chalkboard-teacher',
                'color': 'warning'
            },
            'helper': {
                'title': 'Helpful Hero',
                'description': 'Awarded for sharing 10+ study resources',
                'icon': 'hands-helping',
                'color': 'info'
            },
            'finder': {
                'title': 'Finder Star',
                'description': 'Awarded for helping return 5+ lost items',
                'icon': 'search',
                'color': 'success'
            },
            'active': {
                'title': 'Active User',
                'description': 'Awarded for consistent platform activity',
                'icon': 'bolt',
                'color': 'primary'
            },
            'expert': {
                'title': 'Subject Expert',
                'description': 'Awarded for completing 20+ tutoring sessions',
                'icon': 'graduation-cap',
                'color': 'danger'
            },
            'verified': {
                'title': 'Verified User',
                'description': 'Awarded for verifying university email',
                'icon': 'check-circle',
                'color': 'success'
            }
        }

        badge_info = badge_descriptions.get(badge_type, {})

        badge = Badge.objects.create(
            user=self.user,
            badge_type=badge_type,
            description=badge_info.get('description', '')
        )

        # Send notification about new badge
        from messaging.models import Notification
        Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='New Badge Earned!',
            message=f'You earned the {badge_info.get("title", "Badge")} badge!',
            link='/dashboard/'
        )

        return badge

    def get_leaderboard(self, limit=10):
        """Get top users by points"""
        from .models import CustomUser
        return CustomUser.objects.filter(
            is_verified=True
        ).order_by('-points', '-date_joined')[:limit]

    def get_user_rank(self):
        """Get user's rank based on points"""
        from .models import CustomUser
        users = CustomUser.objects.filter(
            is_verified=True
        ).order_by('-points', '-date_joined')

        for rank, user in enumerate(users, start=1):
            if user == self.user:
                return rank

        return None