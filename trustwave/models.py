# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager

class ProfessionType(models.TextChoices):
    STUDENT = 'student', _('Student')
    TEACHER = 'teacher', _('Teacher')
    MERCHANT = 'merchant', _('Merchant')
    OTHER = 'other', _('Other')

class AccountStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    VALIDATED = 'validated', _('Validated')
    REFUSED = 'refused', _('Refused')

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    # Remove the username field as we'll use email
    username = None
    
    # Custom user fields
    full_name = models.CharField(max_length=255)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        unique=True
    )
    profession = models.CharField(
        max_length=20,
        choices=ProfessionType.choices,
        default=ProfessionType.OTHER
    )
    location = models.CharField(max_length=255)
    id_card = models.ImageField(upload_to='id_cards/', blank=True, null=True)
    supporting_doc = models.FileField(upload_to='supporting_docs/', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    
    objects = CustomUserManager()  # <-- Add this line

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number', 'profession', 'location']
    
    def __str__(self):
        return self.email

class Alert(models.Model):
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='alert_images/', blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    @property
    def votes(self):
        return self.alertvote_set.count()

class AlertVote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'alert')

