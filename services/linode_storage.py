"""Linode Object Storage integration for media and static files"""
import boto3
import os
import streamlit as st
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any
import mimetypes
from datetime import datetime

class LinodeObjectStorage:
    """Manages Linode Object Storage for static files and media"""
    
    def __init__(self):
        self.client = None
        self.bucket_name = os.getenv('LINODE_BUCKET_NAME')
        self.region = os.getenv('LINODE_REGION', 'us-east-1')
        self.endpoint_url = f"https://{self.region}.linodeobjects.com"
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the S3 client for Linode Object Storage"""
        try:
            access_key = os.getenv('LINODE_ACCESS_KEY')
            secret_key = os.getenv('LINODE_SECRET_KEY')
            
            if not all([access_key, secret_key, self.bucket_name]):
                st.warning("Linode Object Storage credentials not configured. Using local storage.")
                return
            
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=self.region
            )
            
            # Test connection
            self.client.head_bucket(Bucket=self.bucket_name)
            st.success("Connected to Linode Object Storage")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                # Bucket doesn't exist, create it
                self._create_bucket()
            else:
                st.error(f"Linode Object Storage error: {e}")
                self.client = None
                
        except NoCredentialsError:
            st.error("Linode Object Storage credentials not found")
            self.client = None
        except Exception as e:
            st.error(f"Failed to initialize Linode Object Storage: {e}")
            self.client = None
    
    def _create_bucket(self):
        """Create the Linode Object Storage bucket"""
        try:
            if self.region == 'us-east-1':
                self.client.create_bucket(Bucket=self.bucket_name)
            else:
                self.client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Set bucket policy for public read access to static files
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/static/*"]
                    }
                ]
            }
            
            import json
            self.client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            st.success(f"Created Linode Object Storage bucket: {self.bucket_name}")
            
        except ClientError as e:
            st.error(f"Failed to create bucket: {e}")
            self.client = None
    
    def upload_file(self, local_file_path: str, object_key: str, public: bool = False) -> Optional[str]:
        """Upload a file to Linode Object Storage"""
        if not self.client:
            return None
        
        try:
            # Determine content type
            content_type, _ = mimetypes.guess_type(local_file_path)
            if content_type is None:
                content_type = 'binary/octet-stream'
            
            extra_args = {
                'ContentType': content_type,
                'Metadata': {
                    'uploaded_at': datetime.now().isoformat(),
                    'app': 'data-registry-platform'
                }
            }
            
            if public:
                extra_args['ACL'] = 'public-read'
            
            # Upload file
            self.client.upload_file(
                local_file_path,
                self.bucket_name,
                object_key,
                ExtraArgs=extra_args
            )
            
            # Return public URL if public
            if public:
                return f"{self.endpoint_url}/{self.bucket_name}/{object_key}"
            else:
                return f"s3://{self.bucket_name}/{object_key}"
                
        except ClientError as e:
            st.error(f"Failed to upload file to Linode: {e}")
            return None
    
    def upload_static_files(self) -> Dict[str, str]:
        """Upload all static files to Linode Object Storage"""
        if not self.client:
            return {}
        
        uploaded_files = {}
        static_dir = "static"
        
        if not os.path.exists(static_dir):
            st.warning("Static directory not found")
            return {}
        
        for root, dirs, files in os.walk(static_dir):
            for file in files:
                local_path = os.path.join(root, file)
                # Create object key maintaining directory structure
                object_key = local_path.replace('\\', '/')
                
                url = self.upload_file(local_path, object_key, public=True)
                if url:
                    uploaded_files[local_path] = url
        
        st.success(f"Uploaded {len(uploaded_files)} static files to Linode Object Storage")
        return uploaded_files
    
    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate a presigned URL for private file access"""
        if not self.client:
            return None
        
        try:
            response = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            st.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def delete_file(self, object_key: str) -> bool:
        """Delete a file from Linode Object Storage"""
        if not self.client:
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            st.error(f"Failed to delete file: {e}")
            return False
    
    def list_files(self, prefix: str = '') -> list:
        """List files in the bucket with optional prefix"""
        if not self.client:
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            st.error(f"Failed to list files: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        if not self.client:
            return {'error': 'Not connected'}
        
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name)
            objects = response.get('Contents', [])
            
            total_size = sum(obj['Size'] for obj in objects)
            total_files = len(objects)
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'bucket_name': self.bucket_name,
                'region': self.region
            }
        except ClientError as e:
            return {'error': str(e)}

# Global instance
linode_storage = LinodeObjectStorage()