import os

import boto3
from botocore.exceptions import ClientError

PREFIX = 'menu/'


def public_url(rel_key):
    if not rel_key:
        return None
    base = os.getenv('MENU_PUBLIC_BASE_URL', '').rstrip('/')
    return f'{base}/{rel_key}'


class MenuStorage:
    """Acceso a S3 limitado al prefijo público `menu/` del bucket existente."""

    def __init__(self, client=None, bucket=None):
        self.bucket = bucket or os.getenv('AWS_S3_BUCKET_NAME')
        if not self.bucket:
            raise ValueError('AWS_S3_BUCKET_NAME no está configurado')
        self.client = client or boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
        )

    @staticmethod
    def full_key(rel_key):
        rel = (rel_key or '').lstrip('/')
        if not rel or '..' in rel.split('/'):
            raise ValueError(f'Clave inválida para la carta: {rel_key!r}')
        return PREFIX + rel

    def put(self, rel_key, body, content_type, cache_control):
        self.client.put_object(
            Bucket=self.bucket,
            Key=self.full_key(rel_key),
            Body=body,
            ContentType=content_type,
            CacheControl=cache_control,
        )

    def get(self, rel_key):
        """Devuelve (bytes, content_type); KeyError si el objeto no existe."""
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=self.full_key(rel_key))
        except ClientError as exc:
            if exc.response.get('Error', {}).get('Code') in ('NoSuchKey', '404', 'NotFound', 'NoSuchBucket'):
                raise KeyError(rel_key) from exc
            raise
        return obj['Body'].read(), obj.get('ContentType') or 'application/octet-stream'

    def delete(self, rel_key):
        self.client.delete_object(Bucket=self.bucket, Key=self.full_key(rel_key))

    def list(self, rel_prefix):
        paginator = self.client.get_paginator('list_objects_v2')
        keys = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.full_key(rel_prefix)):
            for obj in page.get('Contents', []):
                keys.append(obj['Key'][len(PREFIX):])
        return keys


def get_menu_storage():
    """Storage de la app actual; los tests inyectan uno falso en app.extensions['menu_storage']."""
    from flask import current_app
    return current_app.extensions.get('menu_storage') or MenuStorage()
