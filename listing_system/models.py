from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model

# Constants
CATEGORY_CHOICES = [
    ('Home & Garden', 'Home & Garden'),
    ('Electronics', 'Electronics'),
    ('Sports Gear', 'Sports Gear'),
    ('Fashion', 'Fashion'),
    ('Tools', 'Tools'),
    ('Kids & Toys', 'Kids & Toys')
]

User = get_user_model()

class Listing(models.Model):
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    brand = models.CharField(max_length=20)
    condition = models.CharField(max_length=10)
    # pictures = models.ImageField(upload_to='listings/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100)
    availability = models.BooleanField(default=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    PRICE_TYPE_CHOICES = [
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    ]
    
    RENT_PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    price_type = models.CharField(max_length=10, choices=PRICE_TYPE_CHOICES, default='sale', verbose_name='Price Type')
    rent_period = models.CharField(max_length=10, choices=RENT_PERIOD_CHOICES, blank=True, null=True, verbose_name='Rent Period', help_text='Required only if price_type is "rent"')

    def clean(self):
        super().clean()
        if self.price_type == 'rent' and not self.rent_period:
            raise ValidationError({'rent_period': 'Rent period is required when price type is rent'})

    def save(self, *args, **kwargs):
        if self.price_type != 'rent':
            self.rent_period = None
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - ${self.price}"
    
    class Meta:
        ordering = ['-created_at']  # Newest first



class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='listings/')
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)



    def save(self, *args, **kwargs):
        if self.is_primary:
            ListingImage.objects.filter(
                listing=self.listing,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.listing.title}"
