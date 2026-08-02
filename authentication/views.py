# Create your views here.
import logging
import os

import jwt
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import redirect, render
from django.utils import translation
from django.utils.encoding import smart_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext as _
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.contrib import messages
import environ
from django.template.loader import render_to_string
from rest_framework.permissions import AllowAny

from .models import User
from .renderers import UserRenderer
from .serializers import *
from .utils import Util



import environ

v = environ.Env()
environ.Env.read_env()

logger = logging.getLogger(__name__)

from .models import UserSession
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Avg


class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [os.environ.get('APP_SCHEME'), 'http', 'https']

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # print("dadada")
        serializer.is_valid(raise_exception=True)
        logger.info(_('Payload is: %s') % serializer)
        user = serializer.save()

        response_data = {
            "user": serializer.data,
            "message": _("Utilisateur créé avec succès. Veuillez vérifier votre e-mail pour vérification.")
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

class VerifyEmail(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    renderer_classes = [UserRenderer]
    def get2(self, request):
        # Récupérer le Bearer Token dans l'en-tête Authorization
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            raise AuthenticationFailed("En-tête d'autorisation manquant")
        
        # Le token Bearer est généralement sous la forme 'Bearer <token>'
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise AuthenticationFailed("Format de l'en-tête d'autorisation invalide")
        
        token = parts[1]
        
        # Afficher le token (par exemple, dans la réponse)
        #return Response({"token": token})

    def get(self, request):
        token = request.GET.get('token')  # Correction ici
        print("affiche",token)
        if not token:
            return Response({'erreur': _('Jeton non fourni')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
        except jwt.ExpiredSignatureError:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY ,
                algorithms=['HS256'],
                options={'verify_exp': False}  # bypass expiration check
            )
            email = payload.get('email')
            logger.error(_("Lien d'activation expiré."))
            #expired_url = f"http://localhost:3000/verification-mail-expired/{email}"
            expired_url = f"https://pre-prod-ufs-v1.universfrancesucces.com/verification-mail-expired/{email}"
            return redirect(expired_url)
        except jwt.DecodeError:
            logger.error(_('Jeton invalide.'))
            return Response({'erreur': _('Jeton invalide')}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            logger.error(_('User not found.'))
            return Response({'erreur': _('Utilisateur non trouvé')}, status=status.HTTP_404_NOT_FOUND)
        frontend_url = "http://localhost:3000"
        #frontend_url = "https://pre-prod-ufs-v1.universfrancesucces.com"


        if not user.is_verified:
            user.is_verified = True
            user.save()
            success_message = _('Email vérifié avec succès')
            # Envoi de l'email de bienvenue après validation du compte
            Util.send_account_validated_email(user)
        else:
            success_message = _('Email déjà vérifié')

        messages.success(request, success_message)
        if user.is_verified:
            if user.role == "admin":
                redirection_url = f"{frontend_url}/administrateur/login?message={success_message}"
                return redirect(redirection_url)  # Change en fonction de ton URL de connexion

            elif user.role == "parent":
                redirection_url = f"{frontend_url}/parent/login?message={success_message}"
                return redirect(redirection_url)  # Change en fonction de ton URL de connexion

            else:
                redirection_url = f"{frontend_url}/etudiant/login?message={success_message}"
                return redirect(redirection_url)  # Change en fonction de ton URL de connexion

        
        user.is_verified = True
        user.save()
        logger.info(_('Utilisateur activé avec succès..'))
        
        frontend_url = "http://localhost:3000"
        #frontend_url = "https://pre-prod-ufs-v1.universfrancesucces.com"

        if user.is_verified:
            role_redirects = {
                "admin": f"{frontend_url}/administrateur/login",
                "parent": f"{frontend_url}/parent/login",
                "student": f"{frontend_url}/etudiant/login",  # Valeur par défaut
            }

            redirection_url = role_redirects.get(user.role, f"{frontend_url}/etudiant/login")
            return redirect(redirection_url)
        



class ResendVerification(generics.GenericAPIView):

    serializer_class = ResendVerificationSerializer
    renderer_classes = [UserRenderer]


    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_verified:
                return Response({'erreur': _("L'utilisateur est déjà vérifié.")}, status=status.HTTP_400_BAD_REQUEST)
            #domaine = "https://marent.ma"
            #domaine = "http://localhost:8000"
            domaine = "http://207.154.205.225:8000"
            #token = RefreshToken.for_user(user).access_token
            token_obj = AccessToken.for_user(user)
            token_obj.set_exp(from_time=datetime.utcnow(), lifetime=timedelta(days=30))  # custom 30-day lifetime
            token_obj['email'] = user.email
            token = str(token_obj)
            relative_link = reverse("verify-email")
            #relative_link = reverse('email-verify')
            abs_url = f'{domaine}{relative_link}?token={token}'

            Util.send_email_verification(user, None, abs_url)

            response_data = {
                "message": _("E-mail de vérification envoyé.")
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'erreur': _('Utilisateur non trouvé.')}, status=status.HTTP_404_NOT_FOUND)

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    renderer_classes = [UserRenderer]

    def post(self, request):
        print("=====>The request has reached this point.")
        # Pass request into serializer context
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        #Create a Session record for the user
        user = serializer.validated_data['user']
        if user.role == "user":
            print("=====> Create Session history for students only <=====")
            UserSession.objects.create(
                user=user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],  # Truncate if needed
                start_time=timezone.now()
            )
        return Response(serializer.data, status=status.HTTP_200_OK)
    def _get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Update the most recent active session
        if request.user.role == "student":
            open_sessions = UserSession.objects.filter(user=request.user, end_time__isnull=True)
            for session in open_sessions:
                session.end_time = timezone.now()
                session.save()
        return Response({"message": "Vous vous êtes déconnecté avec succès."}, status=status.HTTP_204_NO_CONTENT)

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    renderer_classes = [UserRenderer]
    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.validated_data['email'])
        uid,token=Util.send_password_reset_email(request, user)
        print("from last one :",uid,token)
        return Response({"uid": uid, "token": token}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]
    renderer_classes = [UserRenderer]

    def patch(self, request, uidb64, token, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data['password'])
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'error': _("Le lien de réinitialisation n'est pas valide")}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['password'])
            user.save()
            # Envoi de l'email de notification après réinitialisation
            from authentication.utils import Util
            context_email = {
                'user': user,
                'support_url': 'mailto:support@universfrancesucces.com',
                'app_name': 'Univers France Succes',
            }
            Util.send_email(
                subject="Votre mot de passe a été modifié",
                message="",
                to_email=user.email,
                html_message=render_to_string("password_changed_email.html", context_email)
            )
            return Response({"message": _("Réinitialisation du mot de passe réussie.")}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'erreur': _("Le lien de réinitialisation n'est pas valide")}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [UserRenderer]

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            # Envoi de l'email de notification
            from authentication.utils import Util
            user = self.object
            context_email = {
                'user': user,
                'support_url': 'mailto:support@universfrancesucces.com',
                'app_name': 'Univers France Succes',
            }
            Util.send_email(
                subject="Votre mot de passe a été modifié",
                message="",
                to_email=user.email,
                html_message=render_to_string("password_changed_email.html", context_email)
            )
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Mot de passe mis à jour avec succès',
                'data': []
            }
            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# Add these imports
from rest_framework import generics, permissions, status
from django.shortcuts import get_object_or_404
from .serializers import (
    UserProfileSerializer, 
    UserProfileWithListingsSerializer,
    UpdateProfileSerializer
)
from .models import User

# Add these views at the bottom
class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileWithListingsSerializer
    queryset = User.objects.filter(is_active=True)
    lookup_field = 'username'
    lookup_url_kwarg = 'username'
    
    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username, is_active=True)

class CurrentUserProfileView(generics.RetrieveUpdateAPIView):
    """Authenticated user's own profile (can view and update)"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UpdateProfileView(generics.UpdateAPIView):
    """Update profile details"""
    serializer_class = UpdateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full profile data
        profile_serializer = UserProfileSerializer(instance, context=self.get_serializer_context())
        return Response(profile_serializer.data, status=status.HTTP_200_OK)

class CheckUsernameView(generics.GenericAPIView):
    """Check if username is available"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        username = request.query_params.get('username', '').strip()
        
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(username__iexact=username).exists()
        
        # For authenticated users, exclude their own username
        if request.user.is_authenticated:
            exists = User.objects.filter(username__iexact=username).exclude(id=request.user.id).exists()
        
        return Response({
            'username': username,
            'available': not exists,
            'exists': exists
        })
