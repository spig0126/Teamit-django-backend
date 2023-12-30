import base64
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers

class ImageBase64Field(serializers.Field):
     def to_internal_value(self, data):
          # decode image 
          try: 
               if data == None:
                    return None
               
               image_data = base64.b64decode(data)
               
               # Create an InMemoryUploadedFile from image_data
               image_io = BytesIO(image_data)
               image_file = InMemoryUploadedFile(
                    image_io,
                    None,  # field_name
                    'main.png',  # file_name
                    'image/png',  # content_type
                    image_io.tell,  # size
                    None  # content_type_extra
               )
               return image_file
          except Exception as error:
               raise serializers.ValidationError("Invalid image format")
     
     def to_representation(self, value):
          return value
