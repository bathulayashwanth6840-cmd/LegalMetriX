import os
import cv2
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BarcodeDetector:
    """
    Real-world barcode and QR code detector using OpenCV and pyzbar.
    Supports EAN-13, UPC, Code 128, QR Codes, and other standard formats.
    """
    def detect(self, image_path: str) -> Dict[str, Any]:
        logger.info(f"Initiating barcode and QR code detection for: {image_path}")
        
        response = {
            "barcode": None,
            "barcode_type": None,
            "all_codes": []
        }
        
        # 1. Image validation
        if not image_path or not os.path.exists(image_path):
            logger.error(f"Image path does not exist or is empty: {image_path}")
            return response
            
        try:
            # Load the image using OpenCV
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to read image via OpenCV: {image_path}")
                return response

            # 2. Detect all supported barcodes and QR codes
            # Import pyzbar inside the method so it only fails when called if libraries are missing
            from pyzbar.pyzbar import decode
            decoded_objects = decode(image)
            
            all_codes = []
            for obj in decoded_objects:
                if not obj.data:
                    continue
                try:
                    data_str = obj.data.decode('utf-8')
                except Exception:
                    data_str = str(obj.data)
                
                code_type = str(obj.type)
                all_codes.append({
                    "data": data_str,
                    "type": code_type
                })
                
            response["all_codes"] = all_codes
            
            # 3. Return the first valid product barcode as the primary barcode
            if all_codes:
                primary = all_codes[0]
                response["barcode"] = primary["data"]
                response["barcode_type"] = primary["type"]
                logger.info(f"Barcode detection successful. Found {len(all_codes)} codes. Primary: {response['barcode']} ({response['barcode_type']})")
            else:
                logger.info("No barcodes or QR codes detected in the image.")
                
            return response
            
        except Exception as e:
            # 5. Handle errors safely
            logger.error(f"Error occurred during barcode detection for {image_path}: {e}")
            return response
