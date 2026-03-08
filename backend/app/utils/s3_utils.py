import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import mimetypes

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        self.folder_prefix = 'absence-attachments/'
        self.social_security_prefix = 'social-security-documents/'
    
    def upload_file(self, file, employee_id, original_filename):
        """
        Upload a file to S3 bucket
        
        Args:
            file: FileStorage object from Flask request
            employee_id: ID of the employee
            original_filename: Original filename
            
        Returns:
            dict: Contains s3_key, s3_url, and original_filename
        """
        try:
            print(f"[S3 DEBUG] Starting upload - employee_id: {employee_id}, filename: {original_filename}")
            print(f"[S3 DEBUG] Bucket name: {self.bucket_name}")
            
            if not self.bucket_name:
                raise ValueError("AWS S3 bucket no está configurado. Verifique la variable de entorno AWS_S3_BUCKET_NAME")
            
            if not original_filename:
                raise ValueError("El nombre del archivo no puede estar vacío")
            
            filename = secure_filename(original_filename)
            print(f"[S3 DEBUG] Secure filename: {filename}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"{self.folder_prefix}{employee_id}_{timestamp}_{filename}"
            print(f"[S3 DEBUG] S3 key: {s3_key}")
            
            content_type = file.content_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            print(f"[S3 DEBUG] Content type: {content_type}")
            
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'employee_id': str(employee_id),
                        'original_filename': filename,
                        'uploaded_at': datetime.utcnow().isoformat()
                    }
                }
            )
            
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            print(f"[S3 DEBUG] Upload successful, URL: {s3_url}")
            
            return {
                's3_key': s3_key,
                's3_url': s3_url,
                'original_filename': filename,
                'content_type': content_type
            }
        
        except ClientError as e:
            print(f"[S3 DEBUG] ClientError: {str(e)}")
            raise Exception(f"Error uploading file to S3: {str(e)}")
        except Exception as e:
            print(f"[S3 DEBUG] Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def download_file(self, s3_key):
        """
        Download a file from S3 bucket
        
        Args:
            s3_key: S3 object key
            
        Returns:
            tuple: (file_content, content_type, filename)
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            file_content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            
            metadata = response.get('Metadata', {})
            filename = metadata.get('original_filename', s3_key.split('/')[-1])
            
            return file_content, content_type, filename
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: {s3_key}")
            raise Exception(f"Error downloading file from S3: {str(e)}")
    
    def delete_file(self, s3_key):
        """
        Delete a file from S3 bucket
        
        Args:
            s3_key: S3 object key
            
        Returns:
            bool: True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        
        except ClientError as e:
            raise Exception(f"Error deleting file from S3: {str(e)}")
    
    def generate_presigned_url(self, s3_key, expiration=3600):
        """
        Generate a presigned URL for temporary access to a file
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")
    
    def file_exists(self, s3_key):
        """
        Check if a file exists in S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            bool: True if file exists
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise Exception(f"Error checking file existence: {str(e)}")

s3_service = S3Service()
