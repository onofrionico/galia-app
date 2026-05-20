import boto3
from botocore.exceptions import ClientError
import os
from werkzeug.utils import secure_filename
import mimetypes
import uuid


class ProductImageStorage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        self.products_prefix = 'products/'

    def upload_product_image(self, file, original_filename):
        """
        Upload a product image to S3 bucket.

        Args:
            file: FileStorage object from Flask request
            original_filename: Original filename

        Returns:
            str: Full S3 URL of the uploaded image

        Raises:
            ValueError: If bucket not configured or filename is empty
            Exception: If S3 upload fails
        """
        if not self.bucket_name:
            raise ValueError("AWS S3 bucket no está configurado. Verifique la variable de entorno AWS_S3_BUCKET_NAME")

        if not original_filename:
            raise ValueError("El nombre del archivo no puede estar vacío")

        try:
            # Secure the filename
            filename = secure_filename(original_filename)

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

        except ClientError as e:
            raise Exception(f"Error uploading file to S3: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error uploading file: {str(e)}")


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
