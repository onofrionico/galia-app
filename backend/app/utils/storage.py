import boto3
from botocore.exceptions import ClientError
import os
from werkzeug.utils import secure_filename
import mimetypes
import uuid


class ProductImageStorage:
    def __init__(self):
        self.use_s3 = os.getenv('USE_S3_STORAGE', 'false').lower() == 'true'
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        self.products_prefix = 'products/'

        if self.use_s3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )

    def upload_product_image(self, file, original_filename):
        """
        Upload a product image to S3 bucket or local storage (development).

        Args:
            file: FileStorage object from Flask request
            original_filename: Original filename

        Returns:
            str: Full S3 URL of the uploaded image or local URL

        Raises:
            ValueError: If bucket not configured or filename is empty
            Exception: If upload fails
        """
        if not original_filename:
            raise ValueError("El nombre del archivo no puede estar vacío")

        try:
            # Secure the filename
            filename = secure_filename(original_filename)

            if self.use_s3:
                return self._upload_to_s3(file, filename)
            else:
                return self._upload_local_dev(file, filename)

        except ClientError as e:
            raise Exception(f"Error uploading file: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error uploading file: {str(e)}")

    def _upload_to_s3(self, file, filename):
        """Upload to S3 bucket."""
        if not self.bucket_name:
            raise ValueError("AWS S3 bucket no está configurado. Verifique la variable de entorno AWS_S3_BUCKET_NAME")

        # Generate unique S3 key with UUID
        s3_key = f"{self.products_prefix}{uuid.uuid4().hex}_{filename}"

        # Determine content type
        content_type = file.content_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        # Upload to S3
        self.s3_client.upload_fileobj(
            file,
            self.bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256',
            }
        )

        # Return full S3 URL
        s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
        return s3_url

    def _upload_local_dev(self, file, filename):
        """Upload to local filesystem for development."""
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}_{filename}"

        # For development, return a mock URL (this could point to a local uploads directory)
        # In production, this would store the file locally or in S3
        mock_url = f"https://cdn.mock/images/{self.products_prefix}{unique_filename}"
        return mock_url


# Create singleton instance
_storage = ProductImageStorage()


def upload_product_image(file, filename):
    """
    Upload a product image to S3.

    Args:
        file: FileStorage object from Flask request
        filename: Original filename

    Returns:
        str: Full S3 URL of the uploaded image
    """
    return _storage.upload_product_image(file, filename)
