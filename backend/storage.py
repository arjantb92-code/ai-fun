import os
from werkzeug.utils import secure_filename

class StorageService:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)

    def save_file(self, file, prefix=""):
        """
        Saves a file and returns the public URL.
        Current implementation: Local Filesystem.
        Future implementation: Upload to S3/Supabase.
        """
        filename = f"{prefix}{secure_filename(file.filename)}"
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)
        
        # In a real cloud environment, this would return an https://s3... link
        return f"http://127.0.0.1:5000/static/{filename}"

# Create instances for different types of blobs
avatar_storage = StorageService("avatars")
receipt_storage = StorageService("uploads")
