# Create your models here.
import uuid
from django.db import models
from django.core.validators import RegexValidator, EmailValidator, MinLengthValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import date
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
import string
import random
from decimal import Decimal
import logging
from django.conf import settings
from backend_marent.storage import ProfilePictureStorage

logger = logging.getLogger(__name__)

# Constants
ROLE_CHOICES = [
    ('user', 'User'),
    ('admin', 'Admin'),
]

# Validators
phone_number_validator = RegexValidator(regex=r'^\d{9,15}$', message="Le numéro de téléphone doit comporter entre 9 et 15 chiffres.")
name_validator = RegexValidator(regex=r'^[A-Za-z\- ]+$', message="Le nom doit contenir uniquement des lettres, des tirets et des espaces.")
country_code_validator = RegexValidator(regex=r'^\+\d{1,3}(-\d{1,4})?$', message="Entrez un code pays valide.")
email_validator = EmailValidator(message="Entrez une adresse email valide.")

def capitalize_name(name):
    return ' '.join('-'.join(part.capitalize() for part in subpart.split('-')) for subpart in name.split(' ')) if name else name

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Le champ Email doit être défini')
        email = self.normalize_email(email)
        
        # Check if the role is admin
        if extra_fields.get('role') == 'admin':
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True, db_index=True, validators=[MinLengthValidator(4)])
    email = models.EmailField(max_length=255, unique=True, db_index=True, validators=[email_validator])
    first_name = models.CharField(max_length=100, blank=True, null=True, validators=[name_validator])
    last_name = models.CharField(max_length=100, blank=True, null=True, validators=[name_validator])
    country_code = models.CharField(max_length=10, blank=True, null=True, validators=[country_code_validator])
    phone_number = models.CharField(max_length=15, blank=True, null=True, validators=[phone_number_validator], help_text="entrer le numero de telephone")
    date_of_birth = models.DateField(blank=True, null=True)
    residence_city = models.CharField(max_length=200, blank=True, null=True)
    picture = models.ImageField(upload_to='', blank=True, null=True, storage=ProfilePictureStorage())
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auth_provider = models.CharField(max_length=255, blank=False, null=False, default='email')
    gender = models.CharField(max_length=255, blank=True, null=True)
    # deactivated_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the user was deactivated")
    # is_deleted = models.BooleanField(default=False)
    # deleted_at = models.DateTimeField(null=True, blank=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @staticmethod
    def generate_unique_username(email):
        """Generate a unique username based on email and random characters."""
        base = email.split('@')[0]
        if len(base) < 4:
            base = base + str(random.randint(1000, 9999))
        username = base
        counter = 1
        
        while User.objects.filter(username=username).exists():
            # Add random characters plus counter to ensure uniqueness
            random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            username = f"{base}_{random_chars}{counter}"
            counter += 1
        
        return username

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.generate_unique_username(self.email)
        self.first_name = capitalize_name(self.first_name)
        self.last_name = self.last_name.upper() if self.last_name else self.last_name
        if self.phone_number and not self.country_code:
            raise ValidationError("L'indicatif du pays est requis si un numéro de téléphone est fourni.")
        self.residence_city = capitalize_name(self.residence_city)
        if self.date_of_birth and self.date_of_birth >= date.today():
            raise ValidationError("La date de naissance doit être dans le passé.")
        if self.role not in dict(ROLE_CHOICES):
            raise ValidationError("Rôle non valide sélectionné.")
        
        # Ensure that is_staff and is_superuser are correctly set for admins
        if self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True

        super().save(*args, **kwargs)

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class ProfileMixin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.user.username
    
class RegularUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    accepted_university = models.CharField(max_length=255, blank=True, null=True)
    accepted_program = models.CharField(max_length=255, blank=True, null=True)
    accepted_level = models.CharField(max_length=255, blank=True, null=True)
    destination_city = models.CharField(max_length=255, blank=True, null=True)
    destination_country = models.CharField(max_length=255, blank=True, null=True)
    reference_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    parent_reference_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = self.generate_unique_reference_code()
        if not self.parent_reference_code:
            self.parent_reference_code = self.generate_unique_reference_code()
        super().save(*args, **kwargs)

    def generate_unique_reference_code(self):
        while True:
            reference_code = uuid.uuid4()
            if not Student.objects.filter(reference_code=reference_code).exists() and not Student.objects.filter(parent_reference_code=reference_code).exists():
                return reference_code

    def notify_parents(self, message):
        for parent in self.parents.all():
            send_notification(parent.user.email, message)

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

class Administrator(ProfileMixin):
    class Meta:
        verbose_name = 'Administrator'
        verbose_name_plural = 'Administrators'

def send_notification(email, message):
    # Implement your notification logic here, e.g., sending an email or push notification
    print(f'Notification envoyée a {email}: {message}')





#Create your models here.
class EmailTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return self.name


#this Model is used to track user sessions for analytics purposes.(By Issame Dryab)
class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds")
    last_active = models.DateTimeField(null=True, blank=True)
    active_duration = models.PositiveIntegerField(default=0, help_text="Active duration in seconds")

    
    # Optional metadata (useful for stats)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.end_time and not self.duration:
            self.duration = (self.end_time - self.start_time).seconds
        super().save(*args, **kwargs)