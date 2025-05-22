from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import IntegrityError
from django.core.paginator import Paginator
from .models import CustomUser, Alert, AlertVote, AccountStatus
from .forms import CustomUserCreationForm, CustomAuthenticationForm, AlertForm

def is_admin(user):
    return user.is_admin

def index(request):
    """Home page view"""
    # Get recent alerts
    recent_alerts = Alert.objects.all().order_by('-created_at')[:5]
    
    # Get statistics for the homepage
    stats = {
        'users': CustomUser.objects.filter(status=AccountStatus.VALIDATED).count(),
        'alerts': Alert.objects.count(),
        'votes': AlertVote.objects.count(),
    }
    
    context = {
        'recent_alerts': recent_alerts,
        'stats': stats,
    }
    
    return render(request, 'index.html', context)

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful. Your account is pending approval.")
            return redirect('registration_pending')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})
    
def registration_pending(request):
    """Registration pending view"""
    return render(request, 'registration_pending.html')

def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                # Check if user status is validated
                if user.status != AccountStatus.VALIDATED and not user.is_admin:
                    messages.warning(request, "Your account is pending approval.")
                    return redirect('registration_pending')
                return redirect('index')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

def alerts(request):
    """View all alerts"""
    all_alerts = Alert.objects.all().order_by('-created_at')
    
    # Get filter parameters
    urgency = request.GET.get('urgency', 'all')
    category = request.GET.get('category', 'all')
    sort_by = request.GET.get('sort_by', 'date')
    search = request.GET.get('search', '')
    
    # Apply filters
    if urgency != 'all':
        all_alerts = all_alerts.filter(urgency=urgency)
    
    if category != 'all':
        all_alerts = all_alerts.filter(category=category)
        
    if search:
        all_alerts = all_alerts.filter(title_icontains=search) | all_alerts.filter(descriptionicontains=search) | all_alerts.filter(location_icontains=search)
    
    # Apply sorting
    if sort_by == 'votes':
        # This requires an annotation, but for simplicity we'll handle in Python
        # In a real app, you'd use Django ORM's annotation feature
        all_alerts = sorted(all_alerts, key=lambda a: a.votes, reverse=True)
    elif sort_by == 'urgency':
        urgency_weights = {'high': 3, 'medium': 2, 'low': 1}
        all_alerts = sorted(all_alerts, key=lambda a: urgency_weights.get(a.urgency, 0), reverse=True)
    
    # Get unique categories for filter
    categories = Alert.objects.values_list('category', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(all_alerts, 9)  # 9 alerts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'alerts': page_obj,
        'categories': categories,
        'selected_urgency': urgency,
        'selected_category': category,
        'selected_sort': sort_by,
        'search_term': search
    }
    
    return render(request, 'alerts.html', context)

@login_required
def post_alert(request):
    """Post a new alert"""
    # Check if user is validated
    if request.user.status != AccountStatus.VALIDATED and not request.user.is_admin:
        messages.warning(request, "Your account must be validated to post alerts.")
        return redirect('registration_pending')
    
    if request.method == 'POST':
        form = AlertForm(request.POST, request.FILES)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            messages.success(request, "Alert posted successfully.")
            return redirect('alerts')
    else:
        form = AlertForm()
    
    return render(request, 'post_alert.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    user_alerts = Alert.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'user': request.user,
        'alerts': user_alerts
    }
    return render(request, 'profile.html', context)

@login_required
def vote_alert(request):
    """Vote for an alert via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # Check if user is validated
    if request.user.status != AccountStatus.VALIDATED and not request.user.is_admin:
        return JsonResponse({'error': 'Account not validated'}, status=403)
        
    alert_id = request.POST.get('alert_id')
    alert = get_object_or_404(Alert, id=alert_id)
    
    try:
        # Check if user already voted
        vote, created = AlertVote.objects.get_or_create(user=request.user, alert=alert)
        if not created:
            # User already voted, remove the vote
            vote.delete()
            return JsonResponse({'success': True, 'action': 'removed', 'votes': alert.votes})
        return JsonResponse({'success': True, 'action': 'added', 'votes': alert.votes})
    except IntegrityError:
        return JsonResponse({'error': 'Error processing vote'}, status=500)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard view"""
    pending_users = CustomUser.objects.filter(status=AccountStatus.PENDING).order_by('created_at')
    validated_users = CustomUser.objects.filter(status=AccountStatus.VALIDATED).order_by('full_name')
    refused_users = CustomUser.objects.filter(status=AccountStatus.REFUSED).order_by('full_name')
    
    context = {
        'pending_users': pending_users,
        'validated_users': validated_users,
        'refused_users': refused_users
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def validate_user(request, user_id):
    """Validate a user account"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.status = AccountStatus.VALIDATED
    user.save()
    messages.success(request, f"User {user.full_name} has been validated.")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def refuse_user(request, user_id):
    """Refuse a user account"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.status = AccountStatus.REFUSED
    user.save()
    messages.success(request, f"User {user.full_name} has been refused.")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def view_user_documents(request, user_id):
    """View a user's verification documents"""
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'user_documents.html', {'user': user})

def handler404(request, exception=None):
    """404 Page not found handler"""
    return render(request, '404.html', status=404)