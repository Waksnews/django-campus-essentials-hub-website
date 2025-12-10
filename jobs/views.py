# jobs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Job, JobApplication
from .forms import JobForm, ApplicationForm


def job_list(request):
    """List all jobs"""
    jobs = Job.objects.filter(status='open').order_by('-created_at')

    # Filtering
    category = request.GET.get('category', '')
    if category:
        jobs = jobs.filter(category=category)

    return render(request, 'jobs/list.html', {
        'jobs': jobs,
        'categories': [
            {'value': 'typing', 'name': 'Typing Work', 'count': jobs.filter(category='typing').count(),
             'icon': 'keyboard', 'color': 'primary'},
            {'value': 'design', 'name': 'Design', 'count': jobs.filter(category='design').count(),
             'icon': 'paint-brush', 'color': 'success'},
            {'value': 'errands', 'name': 'Errands', 'count': jobs.filter(category='errands').count(), 'icon': 'running',
             'color': 'warning'},
            {'value': 'academic', 'name': 'Academic Support', 'count': jobs.filter(category='academic').count(),
             'icon': 'graduation-cap', 'color': 'info'},
            {'value': 'photography', 'name': 'Photography', 'count': jobs.filter(category='photography').count(),
             'icon': 'camera', 'color': 'danger'},
            {'value': 'other', 'name': 'Other', 'count': jobs.filter(category='other').count(), 'icon': 'ellipsis-h',
             'color': 'secondary'},
        ]
    })


def job_detail(request, job_id):
    """View job details"""
    job = get_object_or_404(Job, id=job_id)
    applications = None

    if job.user == request.user:
        applications = job.applications.all()

    return render(request, 'jobs/detail.html', {
        'job': job,
        'applications': applications,
        'is_owner': job.user == request.user,
        'has_applied': job.applications.filter(
            applicant=request.user).exists() if request.user.is_authenticated else False,
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
            messages.success(request, 'Job posted successfully!')
            return redirect('jobs:detail', job_id=job.id)
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
            messages.success(request, 'Job updated successfully!')
            return redirect('jobs:detail', job_id=job.id)
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/update.html', {'form': form, 'job': job})


@login_required
def delete_job(request, job_id):
    """Delete a job"""
    job = get_object_or_404(Job, id=job_id, user=request.user)

    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('jobs:list')

    return render(request, 'jobs/confirm_delete.html', {'job': job})


@login_required
def apply_job(request, job_id):
    """Apply for a job"""
    job = get_object_or_404(Job, id=job_id)

    # Check if already applied
    if job.applications.filter(applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('jobs:detail', job_id=job.id)

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, 'Application submitted successfully!')
            return redirect('jobs:detail', job_id=job.id)
    else:
        form = ApplicationForm()

    return render(request, 'jobs/apply.html', {'form': form, 'job': job})


@login_required
def job_applications(request, job_id):
    """View applications for a job (owner only)"""
    job = get_object_or_404(Job, id=job_id, user=request.user)
    applications = job.applications.all()

    return render(request, 'jobs/applications.html', {
        'job': job,
        'applications': applications,
    })


@login_required
def my_jobs(request):
    """View user's jobs"""
    posted_jobs = Job.objects.filter(user=request.user)
    applied_jobs = Job.objects.filter(applications__applicant=request.user)

    return render(request, 'jobs/my_jobs.html', {
        'posted_jobs': posted_jobs,
        'applied_jobs': applied_jobs,
    })


@login_required
def update_application_status(request, app_id):
    """Update application status (owner only)"""
    application = get_object_or_404(JobApplication, id=app_id, job__user=request.user)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['accepted', 'rejected', 'withdrawn']:
            application.status = status
            application.save()
            messages.success(request, f'Application marked as {status}')

    return redirect('jobs:applications', job_id=application.job.id)


@login_required
def withdraw_application(request, app_id):
    """Withdraw an application"""
    application = get_object_or_404(JobApplication, id=app_id, applicant=request.user)

    if request.method == 'POST':
        application.status = 'withdrawn'
        application.save()
        messages.success(request, 'Application withdrawn successfully!')

    return redirect('jobs:my_jobs')