import os
import cv2
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class BarcodeDetector:
    """
    Barcode and QR code detector.

    Uses:
    1. pyzbar for EAN, UPC, CODE128 and other barcode formats
    2. OpenCV QRCodeDetector as a fallback for QR codes
    """

    def detect(self, image_path: str) -> Dict[str, Any]:

        logger.info(
            f"Starting barcode and QR detection for: {image_path}"
        )

        response = {
            "barcode": None,
            "barcode_type": None,
            "all_codes": []
        }

        # -----------------------------------
        # 1. Validate image path
        # -----------------------------------

        if not image_path:
            logger.error("Image path is empty.")
            return response

        if not os.path.exists(image_path):
            logger.error(
                f"Image does not exist: {image_path}"
            )
            return response

        try:

            # -----------------------------------
            # 2. Read image
            # -----------------------------------

            image = cv2.imread(image_path)

            if image is None:
                logger.error(
                    f"OpenCV could not read image: {image_path}"
                )
                return response

            detected_codes: List[Dict[str, str]] = []

            # -----------------------------------
            # 3. Detect barcodes using pyzbar
            # -----------------------------------

            try:

                from pyzbar.pyzbar import decode

                decoded_objects = decode(image)

                for obj in decoded_objects:

                    if not obj.data:
                        continue

                    try:
                        data_str = obj.data.decode("utf-8")
                    except UnicodeDecodeError:
                        data_str = obj.data.decode(
                            "latin-1",
                            errors="replace"
                        )

                    code_type = str(obj.type)

                    detected_codes.append({
                        "data": data_str.strip(),
                        "type": code_type
                    })

                    logger.info(
                        f"Detected {code_type}: {data_str}"
                    )

            except ImportError:

                logger.warning(
                    "pyzbar is not installed. "
                    "Skipping standard barcode detection."
                )

            except Exception as e:

                logger.error(
                    f"pyzbar barcode detection error: {e}"
                )

            # -----------------------------------
            # 4. QR Code fallback using OpenCV
            # -----------------------------------

            try:

                qr_detector = cv2.QRCodeDetector()

                qr_data, bbox, _ = qr_detector.detectAndDecode(
                    image
                )

                if qr_data:

                    # Prevent duplicate QR results
                    already_exists = any(
                        code["data"] == qr_data
                        for code in detected_codes
                    )

                    if not already_exists:

                        detected_codes.append({
                            "data": qr_data.strip(),
                            "type": "QRCODE"
                        })

                        logger.info(
                            f"Detected QR Code: {qr_data}"
                        )

            except Exception as e:

                logger.warning(
                    f"OpenCV QR detection error: {e}"
                )

            # -----------------------------------
            # 5. Save all detected codes
            # -----------------------------------

            response["all_codes"] = detected_codes

            # -----------------------------------
            # 6. Select primary product barcode
            # -----------------------------------

            preferred_types = [
                "EAN13",
                "EAN8",
                "UPCA",
                "UPCE",
                "CODE128",
                "CODE39"
            ]

            primary_code = None

            # First prefer normal product barcodes
            for preferred_type in preferred_types:

                for code in detected_codes:

                    if code["type"].upper() == preferred_type:
                        primary_code = code
                        break

                if primary_code:
                    break

            # Otherwise use the first detected code
            if not primary_code and detected_codes:
                primary_code = detected_codes[0]

            if primary_code:

                response["barcode"] = primary_code["data"]

                response["barcode_type"] = primary_code["type"]

                logger.info(
                    f"Primary code selected: "
                    f"{response['barcode']} "
                    f"({response['barcode_type']})"
                )

            else:

                logger.info(
                    "No barcode or QR code found."
                )

            return response

        except Exception as e:

            logger.exception(
                f"Unexpected barcode detection error: {e}"
            )

            return response
