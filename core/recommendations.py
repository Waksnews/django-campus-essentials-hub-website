# core/recommendations.py
from django.db.models import Q, Count
from accounts.models import CustomUser
from lost_found.models import LostItem
from tutoring.models import Tutor
from jobs.models import Job
from resources.models import Resource
from services.models import Service
import random


class RecommendationEngine:
    def __init__(self, user):
        self.user = user

    def get_recommendations(self, limit=5):
        """Get personalized recommendations for the user"""
        recommendations = []

        # Based on user's course
        if self.user.course:
            course_recommendations = self.get_course_based_recommendations()
            recommendations.extend(course_recommendations)

        # Based on user's activity
        activity_recommendations = self.get_activity_based_recommendations()
        recommendations.extend(activity_recommendations)

        # Based on location
        location_recommendations = self.get_location_based_recommendations()
        recommendations.extend(location_recommendations)

        # Remove duplicates and limit
        unique_recs = []
        seen = set()
        for rec in recommendations:
            rec_id = f"{rec['type']}_{rec['id']}"
            if rec_id not in seen and len(unique_recs) < limit:
                seen.add(rec_id)
                unique_recs.append(rec)

        # Fill with popular items if needed
        if len(unique_recs) < limit:
            popular_recs = self.get_popular_recommendations(limit - len(unique_recs))
            unique_recs.extend(popular_recs)

        return unique_recs

    def get_course_based_recommendations(self):
        """Get recommendations based on user's course"""
        recommendations = []

        # Find tutors for similar courses
        tutors = Tutor.objects.filter(
            user__course__icontains=self.user.course
        ).exclude(user=self.user).order_by('-rating')[:3]

        for tutor in tutors:
            recommendations.append({
                'type': 'tutor',
                'id': tutor.id,
                'title': f"{tutor.user.username} - {tutor.get_primary_subject_display()} Tutor",
                'description': tutor.bio[:100] + '...',
                'score': 0.8,
                'link': f'/tutoring/{tutor.id}/'
            })

        # Find resources for the course
        resources = Resource.objects.filter(
            course_code__icontains=self.user.course[:3]
        ).order_by('-average_rating', '-downloads')[:2]

        for resource in resources:
            recommendations.append({
                'type': 'resource',
                'id': resource.id,
                'title': resource.title,
                'description': f"{resource.get_resource_type_display()} for {resource.course_code}",
                'score': 0.7,
                'link': f'/resources/{resource.id}/'
            })

        return recommendations

    def get_activity_based_recommendations(self):
        """Get recommendations based on user's recent activity"""
        recommendations = []

        # Based on viewed items (simulated)
        viewed_categories = ['electronics', 'documents']
        for category in viewed_categories:
            items = LostItem.objects.filter(
                category=category,
                status='lost'
            ).exclude(user=self.user).order_by('-created_at')[:2]

            for item in items:
                recommendations.append({
                    'type': 'lost_item',
                    'id': item.id,
                    'title': item.title,
                    'description': f"Lost {item.get_category_display()} near {item.location_lost}",
                    'score': 0.6,
                    'link': f'/lost-found/{item.id}/'
                })

        return recommendations

    def get_location_based_recommendations(self):
        """Get recommendations based on user's location"""
        if not self.user.location:
            return []

        recommendations = []

        # Find services near user's location
        services = Service.objects.filter(
            location__icontains=self.user.location.split(',')[0]
        ).order_by('-average_rating')[:2]

        for service in services:
            recommendations.append({
                'type': 'service',
                'id': service.id,
                'title': service.name,
                'description': f"{service.get_category_display()} service",
                'score': 0.7,
                'link': f'/services/{service.id}/'
            })

        # Find jobs near user's location
        jobs = Job.objects.filter(
            location__icontains=self.user.location.split(',')[0],
            status='open'
        ).order_by('-created_at')[:2]

        for job in jobs:
            recommendations.append({
                'type': 'job',
                'id': job.id,
                'title': job.title,
                'description': f"{job.get_category_display()} gig",
                'score': 0.6,
                'link': f'/jobs/{job.id}/'
            })

        return recommendations

    def get_popular_recommendations(self, limit=3):
        """Get popular items as fallback recommendations"""
        recommendations = []

        # Popular tutors
        tutors = Tutor.objects.filter(is_available=True).order_by('-rating')[:2]
        for tutor in tutors:
            recommendations.append({
                'type': 'tutor',
                'id': tutor.id,
                'title': f"Top Tutor: {tutor.user.username}",
                'description': f"{tutor.get_primary_subject_display()} expert",
                'score': 0.9,
                'link': f'/tutoring/{tutor.id}/'
            })

        # Popular resources
        resources = Resource.objects.filter(
            is_approved=True
        ).order_by('-downloads')[:2]

        for resource in resources:
            recommendations.append({
                'type': 'resource',
                'id': resource.id,
                'title': f"Popular: {resource.title}",
                'description': f"Downloaded {resource.downloads} times",
                'score': 0.8,
                'link': f'/resources/{resource.id}/'
            })

        # Urgent jobs
        jobs = Job.objects.filter(
            status='open'
        ).order_by('-created_at')[:1]

        for job in jobs:
            recommendations.append({
                'type': 'job',
                'id': job.id,
                'title': f"Urgent: {job.title}",
                'description': job.description[:100] + '...',
                'score': 0.7,
                'link': f'/jobs/{job.id}/'
            })

        return recommendations[:limit]