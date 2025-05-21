

# Register your models here.
from django.contrib import admin
from .models import CustomUser, Alert, AlertVote

# Register models to make them visible in Django admin
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'profession', 'status', 'created_at')
    list_filter = ('status', 'profession', 'is_admin')
    search_fields = ('email', 'full_name', 'phone_number')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'urgency', 'location', 'user', 'created_at')
    list_filter = ('urgency', 'category')
    search_fields = ('title', 'description', 'location')

@admin.register(AlertVote)
class AlertVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert', 'created_at')