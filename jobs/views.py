from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Job, JobApplication
from .forms import JobForm, ApplicationForm


def job_list(request):
    """List all jobs"""
    jobs = Job.objects.filter(status='open').order_by('-created_at')

    # Filtering
    category = request.GET.get('category', '')
    if category:
        jobs = jobs.filter(category=category)

    # Prepare categories with counts and icons
    categories = []
    for cat_value, cat_name in Job.CATEGORY_CHOICES:
        count = Job.objects.filter(category=cat_value, status='open').count()

        # Simple color mapping (you can move this to template filters later)
        color_map = {
            'typing': 'primary',
            'design': 'success',
            'errands': 'warning',
            'academic': 'info',
            'photography': 'danger',
            'tutoring': 'purple',
            'tech': 'dark',
            'writing': 'secondary',
            'other': 'secondary'
        }
        icon_map = {
            'typing': 'keyboard',
            'design': 'paint-brush',
            'errands': 'running',
            'academic': 'graduation-cap',
            'photography': 'camera',
            'tutoring': 'chalkboard-teacher',
            'tech': 'laptop-code',
            'writing': 'pen-fancy',
            'other': 'ellipsis-h'
        }

        categories.append({
            'value': cat_value,
            'name': cat_name,
            'count': count,
            'icon': icon_map.get(cat_value, 'briefcase'),
            'color': color_map.get(cat_value, 'secondary')
        })

    return render(request, 'jobs/list.html', {
        'jobs': jobs,
        'categories': categories,
        'selected_category': category
    })
def job_detail(request, job_id):
    """View job details"""
    job = get_object_or_404(Job, id=job_id)

    # Get applications if user is owner
    applications = None
    if request.user.is_authenticated and job.user == request.user:
        applications = job.applications.all().order_by('-applied_at')

    # Check if user has applied
    has_applied = False
    user_application = None
    if request.user.is_authenticated:
        has_applied = job.applications.filter(applicant=request.user).exists()
        if has_applied:
            user_application = job.applications.filter(applicant=request.user).first()

    # Get related jobs
    related_jobs = Job.objects.filter(
        category=job.category,
        status='open'
    ).exclude(id=job_id)[:3]

    return render(request, 'jobs/detail.html', {
        'job': job,
        'applications': applications,
        'related_jobs': related_jobs,
        'is_owner': job.user == request.user,
        'has_applied': has_applied,
        'user_application': user_application,
    })


@login_required
def create_job(request):
    """Create a new job"""
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            messages.success(request, '🎉 Job posted successfully!')
            return redirect('jobs:detail', job_id=job.id)
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = JobForm()

    return render(request, 'jobs/create.html', {'form': form})


@login_required
def update_job(request, job_id):
    """Update a job"""
    job = get_object_or_404(Job, id=job_id, user=request.user)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Job updated successfully!')
            return redirect('jobs:detail', job_id=job.id)
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/update.html', {'form': form, 'job': job})


@login_required
def delete_job(request, job_id):
    """Delete a job"""
    job = get_object_or_404(Job, id=job_id, user=request.user)

    if request.method == 'POST':
        job.delete()
        messages.success(request, '🗑️ Job deleted successfully!')
        return redirect('jobs:list')

    return render(request, 'jobs/confirm_delete.html', {'job': job})


@login_required
def apply_job(request, job_id):
    """Apply for a job"""
    job = get_object_or_404(Job, id=job_id)

    # Check if already applied
    if job.applications.filter(applicant=request.user).exists():
        messages.warning(request, '⚠️ You have already applied for this job.')
        return redirect('jobs:detail', job_id=job.id)

    # Check if user is the job owner
    if job.user == request.user:
        messages.warning(request, '❌ You cannot apply to your own job.')
        return redirect('jobs:detail', job_id=job.id)

    # Check if job is open
    if job.status != 'open':
        messages.error(request, '❌ This job is no longer accepting applications.')
        return redirect('jobs:detail', job_id=job.id)

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, '✅ Application submitted successfully!')
            return redirect('jobs:detail', job_id=job.id)
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = ApplicationForm()

    return render(request, 'jobs/apply.html', {'form': form, 'job': job})


@login_required
def job_applications(request, job_id):
    """View applications for a job (owner only)"""
    job = get_object_or_404(Job, id=job_id, user=request.user)
    applications = job.applications.all().order_by('-applied_at')

    return render(request, 'jobs/applications.html', {
        'job': job,
        'applications': applications,
    })


@login_required
def my_jobs(request):
    """View user's jobs"""
    posted_jobs = Job.objects.filter(user=request.user).order_by('-created_at')

    # Get applications with job details
    applications = JobApplication.objects.filter(
        applicant=request.user
    ).select_related('job').order_by('-applied_at')

    return render(request, 'jobs/my_jobs.html', {
        'posted_jobs': posted_jobs,
        'applications': applications,
    })


@login_required
def update_application_status(request, app_id):
    """Update application status (owner only)"""
    application = get_object_or_404(JobApplication, id=app_id, job__user=request.user)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['accepted', 'rejected', 'withdrawn']:
            old_status = application.status
            application.status = status
            application.save()

            # If accepting, update job status
            if status == 'accepted':
                application.job.status = 'in_progress'
                application.job.save()
                # Reject other applications
                JobApplication.objects.filter(
                    job=application.job
                ).exclude(id=app_id).update(status='rejected')

            messages.success(request, f'✅ Application status changed from {old_status} to {status}')

    return redirect('jobs:applications', job_id=application.job.id)


@login_required
def withdraw_application(request, app_id):
    """Withdraw an application"""
    application = get_object_or_404(JobApplication, id=app_id, applicant=request.user)

    if application.status not in ['pending', 'accepted']:
        messages.error(request, '❌ This application cannot be withdrawn.')
        return redirect('jobs:my_jobs')

    if request.method == 'POST':
        application.status = 'withdrawn'
        application.save()
        messages.success(request, '✅ Application withdrawn successfully!')
        return redirect('jobs:my_jobs')

    return render(request, 'jobs/withdraw.html', {'application': application})


# Helper functions
def get_category_icon(category):
    """Get FontAwesome icon for category"""
    icons = {
        'typing': 'keyboard',
        'design': 'paint-brush',
        'errands': 'running',
        'academic': 'graduation-cap',
        'photography': 'camera',
        'tutoring': 'chalkboard-teacher',
        'tech': 'laptop-code',
        'writing': 'pen-fancy',
        'other': 'ellipsis-h'
    }
    return icons.get(category, 'briefcase')


def get_category_color(category):
    """Get Bootstrap color class for category"""
    colors = {
        'typing': 'primary',
        'design': 'success',
        'errands': 'warning',
        'academic': 'info',
        'photography': 'danger',
        'tutoring': 'purple',
        'tech': 'dark',
        'writing': 'secondary',
        'other': 'secondary'
    }
    return colors.get(category, 'secondary')