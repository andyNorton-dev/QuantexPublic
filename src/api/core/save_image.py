from fastapi import UploadFile, HTTPException
import uuid
import boto3
from core.config import settings


class SaveImage:
    ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
    
    def __init__(self, file: UploadFile):
        self.file = file
        self.bucket_name = settings.s3.bucket
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3.endpoint,
            aws_access_key_id=settings.s3.access_key,
            aws_secret_access_key=settings.s3.secret_key,
        )

    def _validate_file_type(self):
        if self.file.content_type not in self.ALLOWED_TYPES:
            raise HTTPException(
                status_code=400, 
                detail="Разрешены только JPEG, PNG, WEBP"
            )

    def _generate_filename(self) -> str:
        file_extension = self.file.filename.split('.')[-1]
        return f"{uuid.uuid4().hex}.{file_extension}"

    async def save_image(self) -> str:
        try:
            self._validate_file_type()
            
            random_name = self._generate_filename()
            file_path = f"uploads/{random_name}"

            self.s3_client.upload_fileobj(
                self.file.file, 
                self.bucket_name, 
                file_path, 
                ExtraArgs={"ACL": "public-read"}
            )

            file_url = f"{settings.s3.endpoint}/{self.bucket_name}/{file_path}"
            
            return file_url

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

