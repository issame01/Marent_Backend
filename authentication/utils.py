# utils.py

from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import threading
import logging
from django.conf import settings
from .models import EmailTemplate
import os
from django.utils.html import strip_tags
from django.core.mail import send_mail


logger = logging.getLogger(__name__)

class EmailThread(threading.Thread):
    def __init__(self, email):
        super().__init__()
        self.email = email
        self.daemon = True  # Allow thread to exit when main thread exits

    def run(self):
        try:
            self.email.send()
            logger.info(f"Email sent to {self.email.to}")
        except Exception as e:
            logger.error(f"Failed to send email to {self.email.to}: {e}", exc_info=True)

class Util:
    @staticmethod
    def send_email_verification(user, password: None, verification_url):
        """Send a verification email to a new user."""
        logger.info(f"Sending verification email to {user.email}")
        subject = "Bienvenue chez Univers France Succes"
        context = {}
        if password:
            context = {
                'verification_url': verification_url,
                'user': user,
                'temp_password': password if hasattr(user, 'role') and user.role == 'admin' else None,
                'password': password if not (hasattr(user, 'role') and user.role == 'admin') else None
            }
            logger.info(f"Email sent to {user.email} and being sent to {verification_url}")
            print(f"Email sent to {user.email} and being sent to {verification_url}")
        else:
            context = {
                'verification_url': verification_url,
                'user': user
            }
            print(f"Email sent to {user.email} and being sent to {verification_url}")
        html_message = render_to_string("verification_email.html", context)
        plain_message = strip_tags(html_message)  # Version texte de l'email

        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email]
        )
        email.content_subtype = "html"  # Indiquer que l'email est en HTML

        # Utilisation de `EmailThread` pour ne pas bloquer l'exécution
        EmailThread(email).start()
        logger.info(f"Verification email dispatched to thread for {user.email}")
    
    @staticmethod
    def send_email(subject, message, to_email, from_email=None, html_message=None):
        """Envoie un e-mail en utilisant EmailMessage et EmailThread, avec support HTML."""
        from_email = from_email or settings.EMAIL_HOST_USER
        logger.info(f"Envoi d'un e-mail à {to_email} avec le sujet : {subject}")

        # Si un message HTML est fourni, on l'utilise comme corps principal
        if html_message:
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=from_email,
                to=[to_email]
            )
            email.content_subtype = "html"
        else:
            # Sinon, on envoie un e-mail texte
            email = EmailMessage(
                subject=subject,
                body=message or '',
                from_email=from_email,
                to=[to_email]
            )
        # Envoi asynchrone
        EmailThread(email).start()
        logger.info(f"E-mail envoyé (thread) à {to_email}")
        return True
    
    @staticmethod
    def send_password_reset_email(request, user):
        """
        Send a password reset link to the user.
        """
        logger.info(f"Sending password reset email to {user.email}")
        domaine="https://pre-prod-ufs-v1.universfrancesucces.com"
        # domaine = "http://localhost:8000"

        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        relative_link = f'/password-reset-confirm/{uid}/{token}/'

        abs_url = f'{domaine}{relative_link}'
        logger.debug(f"Password reset URL: {abs_url}")
        
        # Try to use template if available
        try:
            context = {
                'user': user,
                'reset_url': abs_url,
                'domain': domaine
            }
            html_message = render_to_string("password_reset_email.html", context)
            subject = "Réinitialisation de votre mot de passe"
            Util.send_email(subject, "", user.email, html_message=html_message)
        except Exception as e:
            # Fallback to plain text email
            logger.warning(f"Using fallback plain text email for password reset: {str(e)}")
            email_subject = 'Réinitialisation de votre mot de passe'
            email_body = f'Bonjour {user.first_name},\n\nPour réinitialiser votre mot de passe, veuillez cliquer sur le lien suivant :\n{abs_url}'
            Util.send_email(email_subject, email_body, user.email)
            
        return uid, token
    
    @staticmethod
    def send_templated_email(template_name, recipient_emails, context=None, fallback_subject=None, fallback_message=None):
        """Send an email using a template from the database or filesystem.
        
        Args:
            template_name: The name of the template to use (first looks in DB, then in filesystem)
            recipient_emails: List of recipient email addresses
            context: A dictionary containing values to be inserted into the template
            fallback_subject: Subject to use if template not found
            fallback_message: Message to use if template not found
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        logger.info(f"Sending templated email '{template_name}' to {recipient_emails}")
        if context is None:
            context = {}
            
        # Add common template context
        context['support_email'] = settings.SUPPORT_EMAIL if hasattr(settings, 'SUPPORT_EMAIL') else 'support@universfrancesucces.com'
        context['company_name'] = settings.COMPANY_NAME if hasattr(settings, 'COMPANY_NAME') else 'Univers France Succes'
        context['frontend_url'] = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'https://pre-prod-ufs-v1.universfrancesucces.com'
        
        # First try to find the template in the database
        try:
            db_template = EmailTemplate.objects.get(name=template_name)
            subject = db_template.subject
            
            # If the template content is a path, render from file
            if db_template.content.startswith('/') or db_template.content.endswith('.html'):
                html_message = render_to_string(db_template.content, context)
            else:
                # Otherwise use the content directly
                html_message = db_template.content
                
            # Replace template variables in the HTML
            for key, value in context.items():
                html_message = html_message.replace('{{' + key + '}}', str(value))
                
            success = True
            for recipient in recipient_emails:
                success = success and Util.send_email(subject, None, recipient, html_message=html_message)
            return success
            
        except EmailTemplate.DoesNotExist:
            # If not in database, try to find a file-based template
            logger.info(f"Email template '{template_name}' not found in database, trying filesystem")
            try:
                template_path = f"{template_name}.html"
                html_message = render_to_string(template_path, context)
                # Sujet en français pour payment_success
                if template_name == 'payment_success':
                    subject = fallback_subject or "Confirmation de Paiement"
                else:
                    subject = fallback_subject or f"Notification: {template_name.replace('_', ' ').title()}"
                
                success = True
                for recipient in recipient_emails:
                    success = success and Util.send_email(subject, None, recipient, html_message=html_message)
                return success
                
            except Exception as e:
                # If template not found or rendering fails, fall back to the plain text message
                logger.warning(f"Failed to render template '{template_name}': {str(e)}")
                if fallback_subject and fallback_message:
                    logger.info("Using fallback plain text message")
                    success = True
                    for recipient in recipient_emails:
                        success = success and Util.send_email(fallback_subject, fallback_message, recipient)
                    return success
                else:
                    logger.error("No fallback message provided, email not sent")
                    return False
    
    @staticmethod
    def send_payment_notification(user, payment, status, template_context=None):
        """
        Sends payment notifications based on payment status.
        
        Args:
            user: The User object
            payment: The Payment object
            status: The payment status (completed, failed, requires_action)
            template_context: Additional template context (optional)
        """
        logger.info(f"Sending {status} payment notification to {user.email} for payment {payment.id}")
        
        template_map = {
            'completed': 'payment_success',
            'failed': 'payment_failed',
            'requires_action': 'payment_action_required',
        }
        
        subject_map = {
            'completed': f"Confirmation de Paiement - {payment.service_name}",
            'failed': f"Action Requise: Paiement Échoué - {payment.service_name}",
            'requires_action': f"Action Requise: Authentification de Paiement - {payment.service_name}",
        }
        
        template = template_map.get(status, 'payment_generic')
        fallback_subject = subject_map.get(status, f"Information de Paiement - {payment.service_name}")
        
        # Prepare context
        context = {
            'user': user,
            'payment': payment,
            'payment_date': payment.updated_at.strftime('%Y-%m-%d') if payment.updated_at else "N/A",
            'dashboard_url': f"{settings.FRONTEND_URL}/etudiant/dashboard" if hasattr(settings, 'FRONTEND_URL') else "https://pre-prod-ufs-v1.universfrancesucces.com/etudiant/dashboard",
        }
        
        # Add additional context
        if template_context:
            context.update(template_context)
            
        # Generate a fallback message in case template is not found
        fallback_message = f"""
Bonjour {user.first_name},

Votre paiement de {payment.amount} pour {payment.service_name} a été {status}.

Pour plus d'informations, veuillez vous connecter à votre compte.

Cordialement,
L'équipe Univers France Succes
        """
        
        return Util.send_templated_email(
            template, 
            [user.email], 
            context, 
            fallback_subject=fallback_subject,
            fallback_message=fallback_message
        )

    @staticmethod
    def send_account_validated_email(user):
        """Envoie un email de bienvenue après validation du compte."""
        logger.info(f"Envoi de l'email de bienvenue (compte validé) à {user.email}")
        if hasattr(user, 'role') and user.role == 'admin':
            subject = "Votre compte administrateur a été validé !"
        else:
            subject = "Bienvenue chez Univers France Succès !"
        context = {
            'user': user
        }
        html_message = render_to_string("account_validated_email.html", context)
        Util.send_email(subject, None, user.email, html_message=html_message)
