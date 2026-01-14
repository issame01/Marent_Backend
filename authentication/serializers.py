import logging
from datetime import date

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import ROLE_CHOICES
from .utils import Util

logger = logging.getLogger(__name__)
User = get_user_model()

def set_language(request):
    """
    Set the language for the current session.
    """
    user_language = request.GET.get('language', 'fr')
    translation.activate(user_language)
    request.session[translation.LANGUAGE_SESSION_KEY] = user_language
    return redirect(request.META.get('HTTP_REFERER', '/'))

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user.
    """

    print("<=====================================reached here====================================>")
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'role', 'first_name', 'last_name', 
            'country_code', 'phone_number', 'date_of_birth'
        ]

    def validate(self, attrs):
        role = attrs.get('role', '')
        if role not in dict(ROLE_CHOICES):
            raise serializers.ValidationError(_("Invalid role"))
        
        if 'date_of_birth' in attrs and attrs['date_of_birth'] >= date.today():
            raise serializers.ValidationError(_("La date de naissance doit être dans le passé."))

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        request = self.context.get('request')
        Util.send_email_verification(request, user)
        return user

class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(max_length=555)

class ResendVerificationSerializer(serializers.Serializer):

    """
    Serializer for resending email verification.
    """
    email = serializers.EmailField(required=True)

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    first_name = serializers.CharField(max_length=255, read_only=True)
    last_name = serializers.CharField(max_length=255, read_only=True)
    picture = serializers.SerializerMethodField()
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        return obj.tokens()

    def get_picture(self, obj):
        """
        Method to return the full URL for the user's profile picture.
        """
        request = self.context.get('request')
        return request.build_absolute_uri(obj.picture.url) if obj.picture else None

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        user = authenticate(email=email, password=password)

        if user is None:
            raise AuthenticationFailed(_('Identifiants non valides, réessayez'))
        if not user.is_active:
            raise AuthenticationFailed(_("Compte désactivé, contactez l'administrateur"))
        if not user.is_verified:
            raise AuthenticationFailed(_("L'e-mail n'est pas vérifié"))

        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        """
        Custom method to control the final output format.
        """
        user = instance['user']
        return {
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'picture': self.get_picture(user),
            'tokens': self.get_tokens(user)
        }

class LogoutSerializer(serializers.Serializer):
    """
    Serializer for user logout.
    """
    refresh = serializers.CharField()

    default_error_messages = {
        'bad_token': _('Token is expired or invalid')
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            refresh_token = RefreshToken(self.token)
            refresh_token.blacklist()
        except TokenError:
            self.fail('bad_token')

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_('Aucun utilisateur trouvé avec cette adresse email.'))
        return value

    def save(self):
        request = self.context.get('request')
        user = User.objects.get(email=self.validated_data['email'])
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        current_site = get_current_site(request).domain
        relative_link = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        abs_url = f'http://{current_site}{relative_link}'
        email_body = f'Hi {user.username},\n\nUse the link below to reset your password:\n{abs_url}'
        data = {
            'email_subject': 'Reset your password',
            'email_body': email_body,
            'to_email': user.email,
        }
        print("donehddh")
        Util.send_email(data)
    
class SetNewPasswordSerializer(serializers.Serializer):
    """
    Serializer for setting a new password for 3 profiles.
    """
    password = serializers.CharField(min_length=6, write_only=True)

    class Meta:
        fields = ['password']

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        """
        Validate that the new password meets the necessary criteria.
        """
        validate_password(value)
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        logger.debug(f'User: {user}, Old Password: {attrs["old_password"]}')
        if not user.check_password(attrs['old_password']):
            logger.warning("L'ancien mot de passe est incorrect")
            raise serializers.ValidationError({"old_password": _("L'ancien mot de passe n'est pas correct")})

        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": _("Le nouveau mot de passe ne peut pas être identique à l'ancien mot de passe")})

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user



#=======================================================================> Profile Serializers <======================================================================
class UserProfileSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    member_since = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'display_name', 'picture', 'country_code', 'phone_number',
            'date_of_birth', 'residence_city', 'gender', 'role',
            'member_since', 'is_verified', 'created_at'  # Added created_at
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at']
    
    def get_display_name(self, obj):
        """Generate display name from available fields"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        elif obj.last_name:
            return obj.last_name
        elif obj.username:
            return obj.username
        else:
            return obj.email.split('@')[0]  # Use email prefix
    
    def get_member_since(self, obj):
        """Format the created_at date"""
        return obj.created_at

class UserProfileWithListingsSerializer(UserProfileSerializer):
    listings = serializers.SerializerMethodField()
    listings_count = serializers.SerializerMethodField()
    
    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields + ['listings', 'listings_count']
    
    def get_listings(self, obj):
        try:
            from listing_system.models import Listing
            from listing_system.serializers import ListingSerializer
            
            listings = Listing.objects.filter(seller=obj)[:12]
            return ListingSerializer(listings, many=True, context=self.context).data
        except ImportError:
            return []
        except Exception as e:
            print(f"Error getting listings: {e}")
            return []
    
    def get_listings_count(self, obj):
        try:
            from listing_system.models import Listing
            return Listing.objects.filter(seller=obj).count()
        except ImportError:
            return 0
        except Exception as e:
            print(f"Error counting listings: {e}")
            return 0

# Keep your existing UpdateProfileSerializer as is
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'picture', 
            'country_code', 'phone_number', 'date_of_birth',
            'residence_city', 'gender'
        ]