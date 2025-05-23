from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import Q
from django.core.paginator import Paginator
from .models import CustomUser, Alert, AlertVote, AccountStatus
from .forms import CustomUserCreationForm, CustomAuthenticationForm, AlertForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import CustomUserChangeForm  # You may need to create this form
import re
from django.utils.html import strip_tags

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
        'alert_count': Alert.objects.count(),  # <-- Add this line
    }
    
    return render(request, 'index.html', context)

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        phone_number = request.POST.get('phone_number', '')
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        profession = request.POST.get('profession', '')
        id_card = request.FILES.get('id_card')
        supporting_doc = request.FILES.get('supporting_doc')

        # Phone number: must be 9 digits, numbers only
        if not phone_number.isdigit() or len(phone_number) != 9:
            form.add_error('phone_number', 'Phone number must be exactly 9 digits and contain only numbers.')

        # Full name: max 100 chars, alphabetic only (allow spaces, hyphens, apostrophes)
        if not re.fullmatch(r"[A-Za-zÀ-ÿ\s\-']{1,100}", full_name):
            form.add_error('full_name', 'Name must be alphabetic and up to 100 characters.')

        # Email: must be valid (Django form usually checks this, but double-check)
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            form.add_error('email', 'Enter a valid email address.')

        # Profession: must be selected (not empty)
        if not profession:
            form.add_error('profession', 'Please select your profession.')

        # ID Card: must be PNG or JPEG
        if id_card:
            if not id_card.content_type in ['image/png', 'image/jpeg']:
                form.add_error('id_card', 'ID Card must be a PNG or JPEG image.')

        # Supporting Doc: must be PDF (if provided)
        if supporting_doc:
            if not supporting_doc.content_type == 'application/pdf':
                form.add_error('supporting_doc', 'Supporting document must be a PDF file.')

        if form.is_valid():
            user = form.save(commit=False)
            user.phone_number = phone_number
            user.full_name = full_name
            user.email = email
            user.profession = profession
            user.save()
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
        email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Email validation
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            form.add_error('username', 'Enter a valid email address.')

        # Password validation (required, max length 128)
        if not password or len(password) > 128:
            form.add_error('password', 'Enter your password (max 128 characters).')

        if form.is_valid():
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                # Check if user status is validated
                if user.status != AccountStatus.VALIDATED and not user.is_admin:
                    messages.warning(request, "Your account is pending approval.")
                    return redirect('registration_pending')
                return redirect('index')
            else:
                form.add_error(None, "Invalid email or password.")
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
        all_alerts = all_alerts.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )

    # Apply sorting
    if sort_by == 'votes':
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
        title = request.POST.get('title', '').strip()
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')

        # Sanitize text fields to prevent code injection
        title = strip_tags(title)
        location = strip_tags(location)
        description = strip_tags(description)

        # Title: max 100 chars, allowed chars only
        if not re.fullmatch(r"[A-Za-z0-9À-ÿ\s\-',.!?()]{1,100}", title):
            form.add_error('title', 'Title must be up to 100 characters and contain only letters, numbers, and basic punctuation.')

        # Location: max 100 chars, allowed chars only
        if not re.fullmatch(r"[A-Za-z0-9À-ÿ\s\-',.]{1,100}", location):
            form.add_error('location', 'Location must be up to 100 characters and contain only letters, numbers, and basic punctuation.')

        # Description: max 2000 chars
        if len(description) > 2000:
            form.add_error('description', 'Description must be 2000 characters or less.')

        # Image: must be PNG or JPEG if provided
        if image:
            if not image.content_type in ['image/png', 'image/jpeg']:
                form.add_error('image', 'Image must be a PNG or JPEG file.')

        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.title = title
            alert.location = location
            alert.description = description
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
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        # Manual validation and sanitization
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        profession = request.POST.get('profession', '')
        location = request.POST.get('location', '').strip()

        import re
        from django.utils.html import strip_tags

        # Sanitize text fields
        full_name = strip_tags(full_name)
        location = strip_tags(location)

        # Full name: max 100 chars, alphabetic only
        if not re.fullmatch(r"[A-Za-zÀ-ÿ\s\-']{1,100}", full_name):
            form.add_error('full_name', 'Name must be alphabetic and up to 100 characters.')

        # Email: must be valid
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            form.add_error('email', 'Enter a valid email address.')

        # Phone number: must be 9 digits, numbers only
        if not phone_number.isdigit() or len(phone_number) != 9:
            form.add_error('phone_number', 'Phone number must be exactly 9 digits and contain only numbers.')

        # Profession: must be selected
        if not profession:
            form.add_error('profession', 'Please select your profession.')

        # Location: max 100 chars, allowed chars only
        if not re.fullmatch(r"[A-Za-z0-9À-ÿ\s\-',.]{1,100}", location):
            form.add_error('location', 'Location must be up to 100 characters and contain only letters, numbers, and basic punctuation.')

        if form.is_valid():
            user = form.save(commit=False)
            user.full_name = full_name
            user.email = email
            user.phone_number = phone_number
            user.profession = profession
            user.location = location
            user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Your password was successfully updated!")
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})

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