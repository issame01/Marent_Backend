from storages.backends.s3boto3 import S3Boto3Storage
from storages.backends.s3 import S3Storage
import logging
import os
from django.core.files.storage import Storage
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class CustomS3Storage(S3Boto3Storage):
    """
    Custom S3 storage class that handles file existence checks more gracefully.
    This is the main storage class used for all S3 operations.
    """
    
    def exists(self, name):
        """
        Check if a file exists in the S3 bucket.
        Returns False if the file doesn't exist or if there's an error checking.
        """
        try:
            self.connection.meta.client.head_object(
                Bucket=self.bucket_name,
                Key=self._normalize_name(self._clean_name(name))
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # The object does not exist
                return False
            elif e.response['Error']['Code'] == '403':
                # Permission denied, but we'll treat it as not existing
                logger.warning(
                    f"Permission denied (403) when checking if file exists: {name}. "
                    f"Treating as non-existent."
                )
                return False
            else:
                # Log other errors but don't fail
                logger.error(
                    f"Error checking if file exists: {name}. "
                    f"Error: {e.response['Error']['Code']} - {e.response['Error']['Message']}"
                )
                return False
        except Exception as e:
            logger.error(f"Unexpected error in exists method: {str(e)}")
            return False
    
    def get_available_name(self, name, max_length=None):
        """
        Override the get_available_name method to handle S3 errors gracefully.
        This is called during file upload to find an available filename.
        """
        try:
            # First try the standard approach
            return super().get_available_name(name, max_length)
        except ClientError as e:
            # If we get a 403 error, assume the file doesn't exist and use the name as is
            if e.response['Error']['Code'] == '403':
                logger.warning(
                    f"Permission denied (403) in get_available_name for: {name}. "
                    f"Assuming file doesn't exist and using name as is."
                )
                # Make sure we don't exceed max_length
                if max_length and len(name) > max_length:
                    name = self._truncate_name(name, max_length)
                return name
            # For other errors, re-raise
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_available_name: {str(e)}")
            # Default to using the name as is
            if max_length and len(name) > max_length:
                name = self._truncate_name(name, max_length)
            return name
    
    def _truncate_name(self, name, max_length):
        """Helper to truncate filenames that exceed max_length."""
        if max_length is None or len(name) <= max_length:
            return name
        
        # Split the name into parts
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        
        # Calculate how much we need to truncate
        # Leave room for the extension
        truncation = len(name) - max_length
        
        # Truncate the root of the filename
        truncated_root = file_root[:-truncation]
        
        # Join everything back together
        if dir_name:
            return os.path.join(dir_name, truncated_root + file_ext)
        return truncated_root + file_ext
    
    def save(self, name, content, max_length=None):
        """
        Override the save method to handle S3 errors gracefully.
        """
        try:
            return super().save(name, content, max_length)
        except ClientError as e:
            if e.response['Error']['Code'] == '403':
                logger.warning(
                    f"Permission denied (403) in save for: {name}. "
                    f"Attempting alternative approach."
                )
                # Try a different approach - generate a unique name and try again
                from uuid import uuid4
                file_root, file_ext = os.path.splitext(name)
                unique_name = f"{file_root}_{uuid4().hex[:8]}{file_ext}"
                try:
                    return super().save(unique_name, content, max_length)
                except Exception as inner_e:
                    logger.error(f"Failed alternative save approach: {str(inner_e)}")
                    # If all else fails, return the original name
                    return name
            raise
        except Exception as e:
            logger.error(f"Unexpected error in save method: {str(e)}")
            # If all else fails, return the original name
            return name
    
    def url(self, name):
        """
        Override the url method to handle S3 errors gracefully.
        """
        try:
            return super().url(name)
        except Exception as e:
            logger.error(f"Error generating URL for {name}: {str(e)}")
            # Return a placeholder URL or path
            return f"/s3proxy/{name}"

    def is_name_available(self, name, max_length=None):
        """
        Override is_name_available to handle permission errors gracefully.
        """
        exceeds_max_length = (max_length is not None and len(name) > max_length)
        try:
            return not self.exists(name) and not exceeds_max_length
        except ClientError as e:
            if e.response['Error']['Code'] == '403':
                logger.warning(
                    f"Permission denied (403) in is_name_available for: {name}. "
                    f"Assuming file doesn't exist."
                )
                return not exceeds_max_length
            raise
        except Exception as e:
            logger.error(f"Unexpected error in is_name_available: {str(e)}")
            # Default to assuming the file doesn't exist
            return not exceeds_max_length


# Create specialized storage classes for different use cases
class MediaStorage(CustomS3Storage):
    """Storage for general media files"""
    location = 'media'

class StaticStorage(CustomS3Storage):
    """Storage for static files"""
    location = 'static'

class DocumentStorage(CustomS3Storage):
    """Storage for document files"""
    location = 'documents'

class ProfilePictureStorage(CustomS3Storage):
    """Storage for profile pictures"""
    location = 'profile_pictures'
    
class RentalContractStorage(CustomS3Storage):
    """Storage for rental contracts"""
    location = 'rental_contracts'
    
class CertificateStorage(CustomS3Storage):
    """Storage for certificates"""
    location = 'certificates'
    
class SupportAttachmentsStorage(CustomS3Storage):
    """Storage for support ticket attachments"""
    location = 'support_attachments'
    
class ChatAttachmentsStorage(CustomS3Storage):
    """Storage for chat message attachments"""
    location = 'chat_attachments' 