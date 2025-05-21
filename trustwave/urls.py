
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Public views
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('registration-pending/', views.registration_pending, name='registration_pending'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('alerts/', views.alerts, name='alerts'),
    
    # Authenticated views
    path('post-alert/', views.post_alert, name='post_alert'),
    path('profile/', views.profile, name='profile'),
    path('vote-alert/', views.vote_alert, name='vote_alert'),
    
    # Admin views
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('validate-user/<int:user_id>/', views.validate_user, name='validate_user'),
    path('refuse-user/<int:user_id>/', views.refuse_user, name='refuse_user'),
    path('user-documents/<int:user_id>/', views.view_user_documents, name='view_user_documents'),
]

# Add media url patterns for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
