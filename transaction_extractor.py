import logging
from pathlib import Path
import pdfplumber
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

logger = logging.getLogger(__name__)

class TransactionType(Enum):
    """Enum for different types of transactions."""
    PURCHASE = auto()
    PAYMENT = auto()
    RETURN = auto()

@dataclass
class Transaction:
    """
    A class representing a single transaction from a credit card statement.
    """
    date: datetime
    description: str
    amount: float
    transaction_type: TransactionType
    
    def __str__(self) -> str:
        """String representation of the transaction."""
        return f"{self.date.strftime('%Y-%m-%d')} | {self.description} | ${self.amount:.2f}"


class TransactionExtractor:
    """
    A class to extract transaction data from credit card statement PDFs.
    """
    
    def __init__(self, start_marker: str = "ACCOUNT ACTIVITY", stop_marker: str = "Totals Year-to-Date"):
        """
        Initialize the TransactionExtractor.
        
        Args:
            start_marker (str): The text marker that indicates the start of transactions
            stop_marker (str): The text marker that indicates the end of transactions
        """
        self.start_marker = start_marker
        self.stop_marker = stop_marker
        self._format_start_marker()
    
    def _format_start_marker(self) -> None:
        """
        Format the start marker to match the PDF's formatting.
        In the PDF, each character appears to be duplicated except spaces.
        """
        formatted_marker = ""
        for char in self.start_marker:
            if char != " ":
                formatted_marker += char * 2
            else:
                formatted_marker += char
        self.formatted_start_marker = formatted_marker
    
    def extract_transactions(self, text: str) -> str:
        """
        Extract transaction data from a credit card statement PDF.
        
        Args:
            text (str): The text content to extract transactions from
            
        Returns:
            str: Extracted transaction text
            
        Raises:
            ValueError: If the start or stop markers cannot be found
        """
        # Find the position of the formatted title in the text
        title_pos = text.find(self.formatted_start_marker)
        if title_pos == -1:
            raise ValueError("Could not find start marker in text")
        
        # Get text after start point
        text_after_start = text[title_pos:]
        
        # Find the stop point
        stop_pos = text_after_start.find(self.stop_marker)
        if stop_pos == -1:
            raise ValueError("Could not find stop marker in text")
        
        # Extract text between start and stop points
        extracted_text = text_after_start[:stop_pos].strip()
        
        return extracted_text 

    def extract_purchases(self, text: str) -> str:
        """
        Extract purchases only from a credit card statement PDF.
        
        Args:
            text (str): The text content to extract transactions from
            
        Returns:
            str: Extracted transaction text
            
        Raises:
            ValueError: If the start or stop markers cannot be found
        """
        all_transactions = self.extract_transactions(text)
        # Find the position of the formatted title in the text
        title_pos = all_transactions.find("PURCHASE")
        if title_pos == -1:
            raise ValueError("Could not find PURCHASE in text")
        
        all_purchases_text = all_transactions[title_pos:]
        
        # Split text into lines and filter out empty lines
        # lines = [line.strip() for line in all_purchases_text.split('\n') if line.strip()]
        
        # transactions = []
        # for line in lines:
        #     # Skip lines that don't match transaction pattern (date + description + amount)
        #     if not line[0:5].replace('/', '').isdigit():
        #         continue
                
        #     try:
        #         # Extract date (first 5 chars: MM/DD)
        #         date = line[0:5]
                
        #         # Amount is the last numeric value on the line
        #         amount = None
        #         words = line.split()
        #         for word in reversed(words):
        #             try:
        #                 amount = float(word.replace(',', ''))
        #                 break
        #             except ValueError:
        #                 continue
                
        #         if amount is None:
        #             continue
                    
        #         # Description is everything between date and amount
        #         desc_end = line.rfind(str(amount))
        #         if desc_end == -1:
        #             continue
                    
        #         description = line[5:desc_end].strip()
                
        #         transactions.append(Transaction(
        #             date=datetime.strptime(date, "%m/%d"),
        #             description=description,
        #             amount=amount,
        #             transaction_type=TransactionType.PURCHASE
        #         ))
                
        #     except Exception:
        #         logger.error(f"Failed to parse transaction line: {line}")
        #         continue
                
        # return transactions

        return all_purchases_text