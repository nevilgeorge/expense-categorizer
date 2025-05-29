from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from pathlib import Path
import logging
from transaction_extractor import TransactionExtractor
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

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

# Get the frontend URL from environment variable, default to localhost for development
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

app = FastAPI(
    title="Expense Categorizer API",
    description="API for processing credit card statements and categorizing expenses",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        FRONTEND_URL,             # Production URL from env
        "https://*.vercel.app"    # All Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Read and extract text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
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
    """Send the PDF text to OpenAI API for analysis and categorization."""
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    try:
        logger.info("Sending text to OpenAI API for analysis")
        
        prompt = EXPENSE_CATEGORIZATION_PROMPT.format(statement_text=text)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial statement analyzer that returns only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info("Successfully received response from OpenAI API")
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise

@app.post("/analyze-statement")
async def analyze_statement(file: UploadFile):
    """
    Analyze a credit card statement PDF and return categorized expenses.
    
    Args:
        file (UploadFile): The PDF file to analyze
        
    Returns:
        JSONResponse: A JSON object containing:
            - transactions: List of categorized transactions
            - spend_by_category: Dictionary of total spend by category
            - error: Error message if something went wrong
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        
        try:
            # Process the PDF
            text = read_pdf(str(temp_path))
            transaction_extractor = TransactionExtractor()
            purchases = transaction_extractor.extract_purchases(text)
            
            # Analyze with OpenAI
            result = analyze_with_openai(purchases)
            
            # Calculate spend by category
            spend_by_category = {}
            for purchase in result['transactions']:
                category = purchase['category']
                amount = purchase['amount']
                spend_by_category[category] = spend_by_category.get(category, 0) + amount
            
            return JSONResponse({
                "transactions": result['transactions'],
                "spend_by_category": spend_by_category
            })
            
        finally:
            # Clean up temporary file
            temp_path.unlink()
            
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 