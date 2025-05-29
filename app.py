from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from pathlib import Path
import logging
from transaction_extractor import TransactionExtractor
from main import read_pdf, analyze_with_openai
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the frontend URL from environment variable, default to localhost for development
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

app = FastAPI(
    title="Expense Categorizer API",
    description="API for processing credit card statements and categorizing expenses",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # Production URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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