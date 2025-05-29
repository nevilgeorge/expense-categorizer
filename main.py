import sys
import json
from pathlib import Path
import logging
import os
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber
from transaction_extractor import TransactionExtractor
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

EXPENSE_CATEGORIZATION_PROMPT = """
You are an expert at analyzing credit card statements and categorizing expenses. 
Given the following credit card statement text, please:

1. Extract all transactions with their dates, descriptions, and amounts
2. Categorize each transaction into one of these categories:
   - Food & Dining
   - Shopping
   - Transportation
   - Entertainment
   - Utilities
   - Travel
   - Health & Medical
   - Education
   - Personal Care
   - Other

Format your response as a JSON array of objects, where each object has these fields:

    "date": "YYYY-MM-DD",
    "description": "Transaction description",
    "amount": float,
    "category": "Category name"


If you don't know how to categorize a transaction, use "Other". Please don't make up a category 
or skip any transactions. 


Here is the credit card statement text:

{statement_text}
"""


def read_pdf(file_path: str) -> str:
    """
    Read and extract text from a PDF file using pdfplumber.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the file is not a PDF or is corrupted
    """
    try:
        # Convert string path to Path object and resolve to absolute path
        pdf_path = Path(file_path).resolve()
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
            
        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"File must be a PDF. Got: {pdf_path.suffix}")
        
        logger.info(f"Reading PDF from: {pdf_path}")
        
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if not page_text:
                        logger.warning(f"No text extracted from page {page_num}")
                    text += page_text + "\n"
                except Exception as e:
                    logger.error(f"Error processing page {page_num}: {str(e)}")
                    continue
        
        if not text.strip():
            logger.error("No text was extracted from the PDF")
            raise ValueError("Failed to extract any text from the PDF")
            
        logger.info("Successfully extracted text from PDF")
        return text
        
    except Exception as e:
        logger.error(f"Error reading PDF: {str(e)}")
        raise

def analyze_with_openai(text: str) -> dict:
    """
    Send the PDF text to OpenAI API for analysis and categorization.
    
    Args:
        text (str): The extracted text from the PDF
        
    Returns:
        dict: The categorized transactions as returned by the API
        
    Raises:
        ValueError: If the API key is not set or if the API call fails
    """
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    try:
        logger.info("Sending text to OpenAI API for analysis")
        
        # Prepare the prompt with the statement text
        prompt = EXPENSE_CATEGORIZATION_PROMPT.format(statement_text=text)
        
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using a more cost-effective model
            messages=[
                {"role": "system", "content": "You are a financial statement analyzer that returns only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more consistent results
            response_format={"type": "json_object"}
        )
        
        # Extract and parse the response
        result = json.loads(response.choices[0].message.content)
        logger.info("Successfully received response from OpenAI API")
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise

def main():
    """
    Main function to handle command line arguments and process the PDF.
    """
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    start_point = "ACCOUNT ACTIVITY"
    stop_point = "Totals Year-to-Date"

    transaction_extractor = TransactionExtractor(start_point, stop_point)
    try:
        text = read_pdf(pdf_path)
        purchases = transaction_extractor.extract_purchases(text)
        
    except Exception as e:
        logger.error(f"Failed to process PDF: {str(e)}")
        sys.exit(1)

    result = analyze_with_openai(purchases)
    spend_by_category = {}
    for purchase in result['transactions']:
        category = purchase['category']
        amount = purchase['amount']
        spend_by_category[category] = spend_by_category.get(category, 0) + amount
    
    print(spend_by_category)

if __name__ == "__main__":
    main() 