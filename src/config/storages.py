from storages.backends.s3boto3 import S3Boto3Storage

class MinIOMediaStorage(S3Boto3Storage):
    bucket_name = 'local-bucket-form'
    location = 'media'
    file_overwrite = False
    custom_domain = False

class StaticStorage(S3Boto3Storage):
    bucket_name = 'local-bucket-form'
    location = "static"
    default_acl = None