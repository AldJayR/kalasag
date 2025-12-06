"""
KALASAG - Document Controller
Business logic for Document Issuance module.
Implements FR-3.1, FR-3.2, FR-3.3
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from models.document import DocumentModel
from models.resident import ResidentModel
from utils.validators import validate_required
from utils.pdf_generator import PDFGenerator


class DocumentController:
    """Controller for document issuance operations."""
    
    # Document types and their default fees
    DOCUMENT_TYPES = {
        'Clearance': 50.00,
        'Indigency': 0.00,  # Free for indigent
        'Permit': 100.00,
        'Residency': 50.00,
        'Business Permit': 500.00
    }
    
    # Default output directory for PDFs
    DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'documents')
    
    @staticmethod
    def get_document_types() -> Dict[str, float]:
        """Get available document types and their fees."""
        return DocumentController.DOCUMENT_TYPES.copy()
    
    @staticmethod
    def issue_document(
        resident_id: int,
        doc_type: str,
        purpose: str,
        issued_by: int,
        amount: float = None,
        or_number: str = None,
        generate_pdf: bool = True,
        output_dir: str = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Issue a document to a resident (FR-3.1).
        
        Args:
            resident_id: ID of the resident
            doc_type: Type of document
            purpose: Purpose of the document
            issued_by: User ID of issuing officer
            amount: Amount paid (optional, uses default fee if not provided)
            or_number: Official Receipt number (optional)
            generate_pdf: Whether to generate PDF file
            output_dir: Directory to save PDF (uses default if not provided)
            
        Returns:
            Tuple of (success, message, document_data)
        """
        # Validate document type
        if doc_type not in DocumentController.DOCUMENT_TYPES:
            valid_types = ", ".join(DocumentController.DOCUMENT_TYPES.keys())
            return False, f"Invalid document type. Valid types: {valid_types}", None
        
        # Validate resident exists and is active
        resident = ResidentModel.get_by_id(resident_id)
        if not resident:
            return False, "Resident not found", None
        
        if resident.get('status') != 'Active':
            return False, "Cannot issue document to inactive resident", None
        
        # For indigency certificate, verify indigent status
        if doc_type == 'Indigency' and not resident.get('is_indigent'):
            return False, "Resident is not registered as indigent", None
        
        # Validate purpose
        if not purpose or len(purpose.strip()) < 3:
            return False, "Purpose is required (minimum 3 characters)", None
        
        # Set amount if not provided
        if amount is None:
            amount = DocumentController.DOCUMENT_TYPES[doc_type]
        
        # Issue the document
        result = DocumentModel.issue_document(
            res_id=resident_id,
            doc_type=doc_type,
            purpose=purpose.strip(),
            issued_by=issued_by,
            amount=amount,
            or_number=or_number
        )
        
        if not result or not result.get('doc_id'):
            return False, "Failed to issue document", None
        
        doc_id = result['doc_id']
        
        # Get complete document data
        document = DocumentModel.get_by_id(doc_id)
        if not document:
            return False, "Document created but could not retrieve data", None
        
        # Generate PDF if requested
        if generate_pdf:
            pdf_result = DocumentController.generate_pdf(doc_id, output_dir)
            if not pdf_result[0]:
                # Document issued but PDF failed - still return success with warning
                return True, f"Document issued but PDF generation failed: {pdf_result[1]}", document
            document['pdf_path'] = pdf_result[2]
        
        return True, f"Document issued successfully. Control Number: {document['control_number']}", document
    
    @staticmethod
    def generate_pdf(
        doc_id: int,
        output_dir: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate PDF for an existing document (FR-3.1).
        
        Args:
            doc_id: Document ID
            output_dir: Directory to save PDF
            
        Returns:
            Tuple of (success, message, pdf_path)
        """
        # Get document data
        document = DocumentModel.get_by_id(doc_id)
        if not document:
            return False, "Document not found", None
        
        # Set output directory
        if not output_dir:
            output_dir = DocumentController.DEFAULT_OUTPUT_DIR
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        control_number = document['control_number']
        safe_control = control_number.replace('/', '_').replace(':', '_')
        filename = f"{safe_control}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        try:
            # Generate PDF
            PDFGenerator.generate_document(document, output_path)
            return True, "PDF generated successfully", output_path
        except Exception as e:
            return False, f"PDF generation error: {str(e)}", None
    
    @staticmethod
    def verify_document(control_number: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verify document authenticity by control number (FR-3.2).
        
        Args:
            control_number: Control number to verify
            
        Returns:
            Tuple of (is_valid, message, document_data)
        """
        if not control_number or len(control_number.strip()) < 5:
            return False, "Invalid control number format", None
        
        is_valid, document = DocumentModel.verify_control_number(control_number.strip())
        
        if is_valid and document:
            return True, "Document is authentic and verified", document
        else:
            return False, "Document not found or invalid control number", None
    
    @staticmethod
    def get_document(doc_id: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Tuple of (success, message, document_data)
        """
        document = DocumentModel.get_by_id(doc_id)
        if document:
            return True, "Document found", document
        return False, "Document not found", None
    
    @staticmethod
    def get_document_by_control_number(control_number: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get document by control number.
        
        Args:
            control_number: Control number
            
        Returns:
            Tuple of (success, message, document_data)
        """
        document = DocumentModel.get_by_control_number(control_number)
        if document:
            return True, "Document found", document
        return False, "Document not found", None
    
    @staticmethod
    def get_resident_documents(resident_id: int) -> List[Dict[str, Any]]:
        """
        Get all documents for a resident.
        
        Args:
            resident_id: Resident ID
            
        Returns:
            List of documents
        """
        return DocumentModel.get_resident_documents(resident_id)
    
    @staticmethod
    def get_documents_by_date_range(start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get documents within a date range."""
        return DocumentModel.get_all(start_date=start_date, end_date=end_date)

    @staticmethod
    def search_documents(
        doc_type: str = None,
        resident_name: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search documents with filters (FR-3.3).
        
        Args:
            doc_type: Filter by document type
            resident_name: Filter by resident name (partial match)
            date_from: Filter by start date (YYYY-MM-DD)
            date_to: Filter by end date (YYYY-MM-DD)
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        if resident_name:
            return DocumentModel.search(resident_name)
            
        return DocumentModel.get_all(
            doc_type=doc_type,
            start_date=date_from,
            end_date=date_to,
            limit=limit
        )
    
    @staticmethod
    def get_statistics(
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Get document issuance statistics (FR-3.3).
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Statistics dictionary
        """
        stats = DocumentModel.get_statistics(start_date, end_date)
        
        # Calculate additional metrics
        total_count = stats.get('total_documents', 0)
        if total_count > 0:
            # Calculate percentage by type
            by_type = stats.get('by_type', [])
            for item in by_type:
                item['percentage'] = round((item['count'] / total_count) * 100, 1)
        
        return stats
    
    @staticmethod
    def update_payment(
        doc_id: int,
        amount: float,
        or_number: str
    ) -> Tuple[bool, str]:
        """
        Update payment information for a document (FR-3.3).
        
        Args:
            doc_id: Document ID
            amount: Amount paid
            or_number: Official Receipt number
            
        Returns:
            Tuple of (success, message)
        """
        # Validate amount
        if amount is None or amount < 0:
            return False, "Invalid amount"
        
        # Validate OR number
        if not or_number or len(or_number.strip()) < 1:
            return False, "OR number is required"
        
        # Check document exists
        document = DocumentModel.get_by_id(doc_id)
        if not document:
            return False, "Document not found"
        
        # Update payment
        success = DocumentModel.update_payment(doc_id, amount, or_number.strip())
        
        if success:
            return True, "Payment information updated successfully"
        return False, "Failed to update payment information"
    
    @staticmethod
    def get_fee(doc_type: str) -> float:
        """
        Get the fee for a document type.
        
        Args:
            doc_type: Document type
            
        Returns:
            Fee amount
        """
        return DocumentController.DOCUMENT_TYPES.get(doc_type, 0.0)
    
    @staticmethod
    def check_resident_eligibility(
        resident_id: int,
        doc_type: str
    ) -> Tuple[bool, str]:
        """
        Check if resident is eligible for a document type.
        
        Args:
            resident_id: Resident ID
            doc_type: Document type
            
        Returns:
            Tuple of (is_eligible, reason)
        """
        resident = ResidentModel.get_by_id(resident_id)
        
        if not resident:
            return False, "Resident not found"
        
        if resident.get('status') != 'Active':
            return False, "Resident is not active"
        
        if doc_type == 'Indigency' and not resident.get('is_indigent'):
            return False, "Resident is not registered as indigent"
        
        return True, "Resident is eligible"
    
    @staticmethod
    def get_all_documents(doc_type: str = None) -> List[Dict[str, Any]]:
        """
        Get all issued documents.
        
        Args:
            doc_type: Optional filter by document type
            
        Returns:
            List of document records
        """
        return DocumentModel.get_all(doc_type=doc_type)
