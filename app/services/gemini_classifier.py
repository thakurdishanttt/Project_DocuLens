"""
Document classification service using Google's Gemini AI.

This module provides functionality to classify documents using Google's Gemini generative AI model.
It configures the Gemini model with appropriate safety settings and provides a DocumentClassifier
class that can classify document text into predefined categories.
"""

import google.generativeai as genai
from ..core.logging import logger
from ..utils.ai_config import GEMINI_GENERATION_CONFIG, GEMINI_SAFETY_SETTINGS
from typing import Tuple, Any

class DocumentClassifier:
    """
    Document classifier using Google's Gemini AI model.
    
    This class provides methods to classify document text into predefined categories
    using Google's Gemini generative AI model. It handles model initialization and
    provides an asynchronous method for document classification.
    
    Attributes:
        model (GenerativeModel): Initialized Gemini AI model instance.
    """
    
    def __init__(self):
        """
        Initialize the DocumentClassifier with a Gemini model.
        
        Raises:
            Exception: If there is an error initializing the Gemini model.
        """
        try:
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-002",
                generation_config=GEMINI_GENERATION_CONFIG,
                safety_settings=GEMINI_SAFETY_SETTINGS
            )
            logger.info("Gemini model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

    async def classify_document(self, text: str, classifications: list) -> Tuple[str, float, Any]:
        """
        Classify document text into one of the provided categories using Gemini model.
        
        Args:
            text (str): The document text to classify.
            classifications (list): List of possible classification categories.
            
        Returns:
            Tuple[str, float, Any]: A tuple containing:
                - category (str): The classified category or "unknown"
                - confidence (float): Confidence score between 0 and 1
                - reason (Any): Brief explanation for the classification
                
        Notes:
            Only the first 2000 characters of the document text are used for classification.
        """
        try:
            prompt = f"""You are a document classifier. Given the following document text, classify it into one of these categories: {', '.join(classifications)}. 
            If none match, respond with 'unknown'. Respond with only the category name, a confidence score between 0 and 1, and a brief reason.
            Format: category|confidence|reason
            Document text: {text[:2000]}"""  # Using first 2000 chars for classification
            
            response = await self.model.generate_content_async(prompt)
            result = response.text.strip().split('|')
            
            if len(result) != 3:
                return "unknown", 0.0, "Invalid response format"
                
            category, confidence, reason = result
            return category.strip(), float(confidence), reason.strip()
            
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            return "unknown", 0.0, str(e)
