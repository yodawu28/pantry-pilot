"""OCR tool to extract raw text from receipt images using EasyOCR."""
import base64
import io
from typing import Dict, Any
from PIL import Image
import easyocr
from app.config import settings
from minio import Minio


# Initialize EasyOCR reader (supports Vietnamese and English)
# This is loaded once at module level to avoid reloading on each call
reader = easyocr.Reader(['vi', 'en'], gpu=False)  # Vietnamese + English


async def ocr_extract_text(image_path: str) -> Dict[str, Any]:
    """
    Extract raw text from receipt image using EasyOCR.
    
    Args:
        image_path: MinIO path (minio://bucket/object)
        
    Returns:
        {
            "raw_text": "full extracted text",
            "lines": [
                {"text": "line text", "confidence": 0.95, "bbox": [[x1,y1], [x2,y2], ...]},
                ...
            ],
            "success": true/false,
            "error": "error message if failed"
        }
    """
    try:
        # Parse MinIO path
        if not image_path.startswith("minio://"):
            return {
                "raw_text": "",
                "lines": [],
                "success": False,
                "error": f"Invalid MinIO path: {image_path}"
            }
        
        path_parts = image_path.replace("minio://", "").split("/", 1)
        if len(path_parts) != 2:
            return {
                "raw_text": "",
                "lines": [],
                "success": False,
                "error": f"Invalid MinIO path format: {image_path}"
            }
        
        bucket_name, object_name = path_parts
        
        # Fetch image from MinIO
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        
        response = client.get_object(bucket_name, object_name)
        image_bytes = response.read()
        response.close()
        response.release_conn()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Run EasyOCR
        results = reader.readtext(image, detail=1)  # detail=1 returns bbox and confidence
        
        # Format results - convert numpy types to Python native types
        lines = []
        raw_text_parts = []
        
        for bbox, text, confidence in results:
            # Convert numpy arrays/types to Python lists/floats
            bbox_list = [[float(x), float(y)] for x, y in bbox]
            
            lines.append({
                "text": text,
                "confidence": float(confidence),
                "bbox": bbox_list
            })
            raw_text_parts.append(text)
        
        raw_text = "\n".join(raw_text_parts)
        
        return {
            "raw_text": raw_text,
            "lines": lines,
            "success": True,
            "error": None
        }
        
    except Exception as e:
        return {
            "raw_text": "",
            "lines": [],
            "success": False,
            "error": f"OCR extraction failed: {str(e)}"
        }
