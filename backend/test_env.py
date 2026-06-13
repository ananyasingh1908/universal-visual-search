import os
import ocr_service

print('ENV_KEY_PRESENT:', bool(os.getenv('GOOGLE_CLOUD_VISION_API_KEY')))
print('ocr_service._get_google_vision_api_key():', repr(ocr_service._get_google_vision_api_key()))
