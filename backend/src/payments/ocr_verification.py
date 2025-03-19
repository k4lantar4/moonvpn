# Disable OpenCV import due to compatibility issues
OPENCV_AVAILABLE = False
import logging
logging.warning("OpenCV not available. OCR verification will be limited.")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    import logging
    logging.warning("Tesseract not available. OCR verification will be disabled.")

from PIL import Image
import io
import re
import logging
from django.conf import settings
from .models import CardPayment
import traceback

logger = logging.getLogger(__name__)

class ReceiptOCRProcessor:
    """Process payment receipts using OCR to extract and verify payment information"""
    
    def __init__(self):
        # Configure Tesseract path from settings if provided
        if TESSERACT_AVAILABLE:
            tesseract_cmd = getattr(settings, 'TESSERACT_CMD_PATH', 'tesseract')
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.ocr_enabled = OPENCV_AVAILABLE and TESSERACT_AVAILABLE
        if not self.ocr_enabled:
            logger.warning("OCR verification is disabled due to missing dependencies.")
        
        # Regex patterns for extracting information
        self.amount_pattern = r'مبلغ[:\s]*([\d,]+)'
        self.card_pattern = r'کارت[:\s]*(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})'
        self.ref_pattern = r'پیگیری[:\s]*(\d+)'
        self.date_pattern = r'\d{4}/\d{2}/\d{2}'
        self.time_pattern = r'\d{2}:\d{2}:\d{2}'
        
        # OCR configuration
        self.ocr_config = r'--oem 3 --psm 6 -l fas+eng'
        
        # Image preprocessing parameters
        self.kernel_size = getattr(settings, 'OCR_KERNEL_SIZE', (1, 1))
        self.threshold_block_size = getattr(settings, 'OCR_THRESHOLD_BLOCK_SIZE', 11)
        self.threshold_c = getattr(settings, 'OCR_THRESHOLD_C', 2)
    
    def preprocess_image(self, image_data):
        """
        Preprocess the image for better OCR results
        
        Args:
            image_data: Raw image data
            
        Returns:
            Preprocessed image
        """
        if not self.ocr_enabled:
            return None
            
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get black and white image
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            # Apply noise reduction
            kernel = np.ones((1, 1), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            return opening
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None
    
    def extract_text(self, image):
        """
        Extract text from the preprocessed image
        
        Args:
            image: Preprocessed image
            
        Returns:
            Extracted text
        """
        if not self.ocr_enabled or image is None:
            return ""
            
        try:
            # Use Tesseract to extract text
            text = pytesseract.image_to_string(image, lang='fas+eng')
            return text
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def extract_payment_info(self, text):
        """
        Extract payment information from the OCR text
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with extracted payment information
        """
        if not text:
            return {}
            
        result = {}
        
        # Extract amount
        amount_match = re.search(self.amount_pattern, text)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            try:
                result['amount'] = float(amount_str)
            except ValueError:
                pass
        
        # Extract transaction ID
        transaction_id_match = re.search(self.transaction_id_pattern, text)
        if transaction_id_match:
            result['transaction_id'] = transaction_id_match.group(1)
        
        # Extract date
        date_match = re.search(self.date_pattern, text)
        if date_match:
            result['date'] = date_match.group(1)
        
        # Extract time
        time_match = re.search(self.time_pattern, text)
        if time_match:
            result['time'] = time_match.group(1)
        
        return result
    
    def verify_payment(self, payment_id, receipt_image):
        """
        Verify a payment receipt using OCR
        
        Args:
            payment_id: ID of the payment to verify
            receipt_image: Receipt image data
            
        Returns:
            Tuple of (is_verified, verification_details)
        """
        if not self.ocr_enabled:
            logger.warning("OCR verification is disabled. Skipping verification.")
            return True, {"message": "OCR verification is disabled. Manual verification required."}
            
        try:
            # Get payment details from database
            try:
                payment = CardPayment.objects.get(id=payment_id)
            except CardPayment.DoesNotExist:
                return False, {"error": "Payment not found"}
            
            # Process the image
            processed_image = self.preprocess_image(receipt_image)
            if processed_image is None:
                return False, {"error": "Failed to process receipt image"}
            
            # Extract text from image
            text = self.extract_text(processed_image)
            if not text:
                return False, {"error": "Failed to extract text from receipt"}
            
            # Extract payment information
            payment_info = self.extract_payment_info(text)
            if not payment_info:
                return False, {"error": "Failed to extract payment information"}
            
            # Verify amount
            if 'amount' in payment_info and abs(payment_info['amount'] - payment.amount) > 1:
                return False, {"error": "Payment amount does not match"}
            
            # Verify transaction ID if available
            if 'transaction_id' in payment_info and payment.transaction_id and payment_info['transaction_id'] != payment.transaction_id:
                return False, {"error": "Transaction ID does not match"}
            
            # If we got here, the payment is verified
            return True, {"message": "Payment verified successfully", "extracted_info": payment_info}
            
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False, {"error": f"Verification error: {str(e)}"} 