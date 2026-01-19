import io
from typing import Tuple
from PIL import Image
from app.config import settings


class VisionService:
    """
    Image preprocessing for better OCR/vision model accuracy.

    Applies:
    - Contrast enhancement
    - Denoising
    - Rotation correction
    - Resizing to optimal dimensions
    """

    def __init__(self, max_size: int = 2048):
        self.max_size = max_size

    async def preprocess(self, image_bytes: bytes) -> bytes:
        """
        Preprocess image for better extraction.

        Minimal preprocessing to preserve color and text clarity for vision models.

        Args:
            image_bytes: Raw image bytes from storage

        Returns:
            Preprocessed image bytes
        """

        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # Keep original color - vision models work better with color images
        # Only resize if too large
        width, height = image.size

        if max(width, height) > self.max_size:
            scale = self.max_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to RGB if needed (some images are RGBA or palette mode)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Save as JPEG
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=95)

        return output.getvalue()

    def validate_image(self, image_bytes: bytes) -> Tuple[bool, str]:
        """
        Validate image quality before processing.

        Returns:
            (is_valid, message)
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))

            if image.size[0] < 100 or image.size[1] < 100:
                return False, "Image too small (min 100x100px)"

            if len(image_bytes) > 10 * 1024 * 1024:
                return False, "Image too large (max 10MB)"

            # format
            if image.format not in settings.image_format:
                return False, f"Unsupported format: {image.format}"

            return True, "OK"

        except Exception as e:
            return False, f"Invalid image: {str(e)}"
