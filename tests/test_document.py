"""
KALASAG - Test Suite for Document Module
TDD tests for Document Issuance.
Tests FR-3.1, FR-3.2, FR-3.3
"""

import pytest
import sys
import os
import tempfile
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from database import init_database, seed_default_data
from models.document import DocumentModel
from models.resident import ResidentModel
from controllers.document_controller import DocumentController
from utils.pdf_generator import PDFGenerator


# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="module")
def setup_database():
    """Set up test database."""
    database.DATABASE_PATH = "test_kalasag_document.db"
    
    # Remove existing test database
    if os.path.exists("test_kalasag_document.db"):
        os.remove("test_kalasag_document.db")
    
    init_database()
    seed_default_data()
    
    yield
    
    # Cleanup
    if os.path.exists("test_kalasag_document.db"):
        os.remove("test_kalasag_document.db")


@pytest.fixture
def sample_resident(setup_database):
    """Create a sample active resident."""
    res_id = ResidentModel.create(
        first_name="Juan",
        middle_name="Santos",
        last_name="Dela Cruz",
        birthdate="1990-05-15",
        sex="Male",
        civil_status="Single",
        status="Active",
        is_indigent=False
    )
    return res_id


@pytest.fixture
def indigent_resident(setup_database):
    """Create a sample indigent resident."""
    res_id = ResidentModel.create(
        first_name="Maria",
        middle_name="Clara",
        last_name="Santos",
        birthdate="1985-03-20",
        sex="Female",
        civil_status="Married",
        status="Active",
        is_indigent=True
    )
    return res_id


@pytest.fixture
def inactive_resident(setup_database):
    """Create a sample inactive resident."""
    res_id = ResidentModel.create(
        first_name="Pedro",
        last_name="Garcia",
        status="Moved Out"
    )
    return res_id


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for PDF output."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup temp directory and files
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


# ============================================
# DOCUMENT MODEL TESTS
# ============================================

class TestDocumentModel:
    """Test Document Model operations."""
    
    def test_issue_document_clearance(self, setup_database, sample_resident):
        """FR-3.1: Test issuing a Barangay Clearance."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Employment"
        )
        
        assert result['doc_id'] is not None
        assert result['doc_id'] > 0
        assert result['control_number'] is not None
        assert result['control_number'].startswith("CLR-")
    
    def test_issue_document_indigency(self, setup_database, indigent_resident):
        """FR-3.1: Test issuing a Certificate of Indigency."""
        result = DocumentModel.issue_document(
            res_id=indigent_resident,
            doc_type="Indigency",
            purpose="Medical Assistance"
        )
        
        assert result['doc_id'] is not None
        assert result['control_number'].startswith("IND-")
    
    def test_issue_document_with_or_number(self, setup_database, sample_resident):
        """FR-3.3: Test issuing document with O.R. number and amount."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Travel",
            amount=50.00,
            or_number="OR-2025-001"
        )
        
        # Verify the document was logged with payment info
        doc = DocumentModel.get_by_id(result['doc_id'])
        assert doc['amount'] == 50.00
        assert doc['or_number'] == "OR-2025-001"
    
    def test_control_number_format(self, setup_database, sample_resident):
        """FR-3.2: Test control number format (PREFIX-YEAR-SEQUENCE)."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Test"
        )
        
        year = datetime.now().strftime("%Y")
        # Format: CLR-YYYY-XXXXX
        assert f"CLR-{year}-" in result['control_number']
    
    def test_control_number_uniqueness(self, setup_database, sample_resident):
        """FR-3.2: Test that control numbers are unique."""
        result1 = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Test 1"
        )
        
        result2 = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Test 2"
        )
        
        assert result1['control_number'] != result2['control_number']
    
    def test_get_document_by_id(self, setup_database, sample_resident):
        """Test retrieving document by ID."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Retrieval Test"
        )
        
        doc = DocumentModel.get_by_id(result['doc_id'])
        
        assert doc is not None
        assert doc['doc_id'] == result['doc_id']
        assert doc['purpose'] == "Retrieval Test"
    
    def test_get_document_by_control_number(self, setup_database, sample_resident):
        """Test retrieving document by control number."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Control Number Test"
        )
        
        doc = DocumentModel.get_by_control_number(result['control_number'])
        
        assert doc is not None
        assert doc['control_number'] == result['control_number']
    
    def test_get_resident_documents(self, setup_database, sample_resident):
        """Test getting all documents for a resident."""
        # Issue multiple documents
        DocumentModel.issue_document(res_id=sample_resident, doc_type="Clearance", purpose="Test 1")
        DocumentModel.issue_document(res_id=sample_resident, doc_type="Residency", purpose="Test 2")
        
        docs = DocumentModel.get_resident_documents(sample_resident)
        
        assert len(docs) >= 2
        assert all(d['res_id'] == sample_resident for d in docs)
    
    def test_verify_control_number_valid(self, setup_database, sample_resident):
        """Test verifying a valid control number."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Verification Test"
        )
        
        verify_result = DocumentModel.verify_control_number(result['control_number'])
        
        assert verify_result['valid'] is True
        assert verify_result['document'] is not None
    
    def test_verify_control_number_invalid(self, setup_database):
        """Test verifying an invalid control number."""
        result = DocumentModel.verify_control_number("FAKE-2025-99999")
        
        assert result['valid'] is False
        assert result['document'] is None
    
    def test_get_statistics(self, setup_database, sample_resident):
        """Test getting document statistics."""
        # Issue some documents
        DocumentModel.issue_document(res_id=sample_resident, doc_type="Clearance", purpose="Stats Test")
        
        stats = DocumentModel.get_statistics()
        
        assert 'total_issued' in stats
        assert 'by_type' in stats
        assert 'total_revenue' in stats
    
    def test_issue_indigency_non_indigent_fails(self, setup_database, sample_resident):
        """Test that non-indigent residents cannot get indigency certificate."""
        with pytest.raises(ValueError):
            DocumentModel.issue_document(
                res_id=sample_resident,
                doc_type="Indigency",
                purpose="Test"
            )
    
    def test_issue_document_invalid_type_fails(self, setup_database, sample_resident):
        """Test that invalid document types are rejected."""
        with pytest.raises(ValueError):
            DocumentModel.issue_document(
                res_id=sample_resident,
                doc_type="InvalidType",
                purpose="Test"
            )
    
    def test_issue_document_nonexistent_resident_fails(self, setup_database):
        """Test that issuing to non-existent resident fails."""
        with pytest.raises(ValueError):
            DocumentModel.issue_document(
                res_id=99999,
                doc_type="Clearance",
                purpose="Test"
            )


# ============================================
# DOCUMENT CONTROLLER TESTS
# ============================================

class TestDocumentController:
    """Test Document Controller operations."""
    
    def test_issue_document_success(self, setup_database, sample_resident, temp_output_dir):
        """Test successful document issuance via controller."""
        success, message, result = DocumentController.issue_document(
            resident_id=sample_resident,
            doc_type="Clearance",
            purpose="Controller Test",
            issued_by=1,
            generate_pdf=False
        )
        
        assert success is True
        assert result is not None
        assert 'doc_id' in result
        assert 'control_number' in result
    
    def test_issue_document_invalid_type(self, setup_database, sample_resident):
        """Test issuing document with invalid type."""
        success, message, result = DocumentController.issue_document(
            resident_id=sample_resident,
            doc_type="InvalidType",
            purpose="Test",
            issued_by=1,
            generate_pdf=False
        )
        
        assert success is False
        assert result is None
    
    def test_issue_document_inactive_resident(self, setup_database, inactive_resident):
        """Test that inactive residents cannot get documents."""
        success, message, result = DocumentController.issue_document(
            resident_id=inactive_resident,
            doc_type="Clearance",
            purpose="Test",
            issued_by=1,
            generate_pdf=False
        )
        
        assert success is False
    
    def test_issue_document_nonexistent_resident(self, setup_database):
        """Test issuing document for non-existent resident."""
        success, message, result = DocumentController.issue_document(
            resident_id=99999,
            doc_type="Clearance",
            purpose="Test",
            issued_by=1,
            generate_pdf=False
        )
        
        assert success is False
    
    def test_issue_indigency_non_indigent(self, setup_database, sample_resident):
        """Test that non-indigent residents cannot get indigency cert."""
        success, message, result = DocumentController.issue_document(
            resident_id=sample_resident,
            doc_type="Indigency",
            purpose="Test",
            issued_by=1,
            generate_pdf=False
        )
        
        assert success is False
    
    def test_issue_indigency_success(self, setup_database, indigent_resident):
        """Test successful indigency certificate issuance."""
        success, message, result = DocumentController.issue_document(
            resident_id=indigent_resident,
            doc_type="Indigency",
            purpose="Medical",
            issued_by=1,
            generate_pdf=False
        )
        
        assert success is True
    
    def test_get_document_types(self, setup_database):
        """Test getting available document types."""
        types = DocumentController.get_document_types()
        
        assert isinstance(types, dict)
        assert "Clearance" in types
        assert "Indigency" in types
    
    def test_get_document_types_has_fees(self, setup_database):
        """Test that document types include fees."""
        types = DocumentController.get_document_types()
        
        assert types['Clearance'] >= 0
        assert types['Indigency'] == 0  # Free for indigent
    
    def test_issue_with_payment(self, setup_database, sample_resident):
        """Test issuing document with payment info."""
        success, message, result = DocumentController.issue_document(
            resident_id=sample_resident,
            doc_type="Clearance",
            purpose="Payment Test",
            issued_by=1,
            amount=50.00,
            or_number="OR-TEST-001",
            generate_pdf=False
        )
        
        assert success is True
        assert result['amount'] == 50.00
        assert result['or_number'] == "OR-TEST-001"
    
    def test_issue_document_short_purpose_fails(self, setup_database, sample_resident):
        """Test that short purpose is rejected."""
        success, message, result = DocumentController.issue_document(
            resident_id=sample_resident,
            doc_type="Clearance",
            purpose="AB",  # Too short
            issued_by=1,
            generate_pdf=False
        )
        
        assert success is False


# ============================================
# PDF GENERATION TESTS
# ============================================

class TestPDFGeneration:
    """Test PDF generation functionality."""
    
    def test_generate_clearance_pdf(self, setup_database, sample_resident, temp_output_dir):
        """FR-3.1: Test generating Clearance PDF."""
        # Issue document first
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="PDF Test"
        )
        
        doc = DocumentModel.get_by_id(result['doc_id'])
        output_path = os.path.join(temp_output_dir, f"{result['control_number'].replace('/', '_')}.pdf")
        
        pdf_path = PDFGenerator.generate_clearance(doc, output_path)
        
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
    
    def test_generate_indigency_pdf(self, setup_database, indigent_resident, temp_output_dir):
        """FR-3.1: Test generating Indigency PDF."""
        result = DocumentModel.issue_document(
            res_id=indigent_resident,
            doc_type="Indigency",
            purpose="PDF Test"
        )
        
        doc = DocumentModel.get_by_id(result['doc_id'])
        output_path = os.path.join(temp_output_dir, f"{result['control_number'].replace('/', '_')}.pdf")
        
        pdf_path = PDFGenerator.generate_indigency(doc, output_path)
        
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
    
    def test_generate_residency_pdf(self, setup_database, sample_resident, temp_output_dir):
        """FR-3.1: Test generating Residency PDF."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Residency",
            purpose="PDF Test"
        )
        
        doc = DocumentModel.get_by_id(result['doc_id'])
        output_path = os.path.join(temp_output_dir, f"{result['control_number'].replace('/', '_')}.pdf")
        
        pdf_path = PDFGenerator.generate_residency(doc, output_path)
        
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
    
    def test_generate_document_auto(self, setup_database, sample_resident, temp_output_dir):
        """Test auto-detection of document type for PDF generation."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Auto Test"
        )
        
        doc = DocumentModel.get_by_id(result['doc_id'])
        output_path = os.path.join(temp_output_dir, f"{result['control_number'].replace('/', '_')}.pdf")
        
        pdf_path = PDFGenerator.generate_document(doc, output_path)
        
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
    
    def test_pdf_contains_control_number(self, setup_database, sample_resident, temp_output_dir):
        """FR-3.2: Test that PDF is generated with control number."""
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Control Number Test"
        )
        
        doc = DocumentModel.get_by_id(result['doc_id'])
        output_path = os.path.join(temp_output_dir, f"{result['control_number'].replace('/', '_')}.pdf")
        
        pdf_path = PDFGenerator.generate_clearance(doc, output_path)
        
        # PDF was generated (content verification would need PDF reading)
        assert pdf_path is not None
        assert os.path.exists(pdf_path)


# ============================================
# INTEGRATION TESTS
# ============================================

class TestDocumentIntegration:
    """Integration tests for document workflow."""
    
    def test_full_document_workflow(self, setup_database, sample_resident, temp_output_dir):
        """Test complete document issuance workflow."""
        # 1. Get available document types and fees
        doc_types = DocumentController.get_document_types()
        assert "Clearance" in doc_types
        fee = doc_types["Clearance"]
        
        # 2. Issue document with payment via controller
        success, message, result = DocumentController.issue_document(
            resident_id=sample_resident,
            doc_type="Clearance",
            purpose="Full Workflow Test",
            issued_by=1,
            amount=fee,
            or_number="OR-TEST-001",
            generate_pdf=False
        )
        assert success is True
        
        # 3. Verify control number
        verify_result = DocumentModel.verify_control_number(result['control_number'])
        assert verify_result['valid'] is True
        
        # 4. Generate PDF
        doc = DocumentModel.get_by_id(result['doc_id'])
        output_path = os.path.join(temp_output_dir, f"{result['control_number'].replace('/', '_')}.pdf")
        pdf_path = PDFGenerator.generate_clearance(doc, output_path)
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
    
    def test_multiple_documents_same_resident(self, setup_database, sample_resident):
        """Test issuing multiple documents to same resident."""
        # Issue multiple document types
        doc_types = ["Clearance", "Residency"]
        control_numbers = []
        
        for doc_type in doc_types:
            success, message, result = DocumentController.issue_document(
                resident_id=sample_resident,
                doc_type=doc_type,
                purpose=f"{doc_type} Test",
                issued_by=1,
                generate_pdf=False
            )
            assert success is True
            control_numbers.append(result['control_number'])
        
        # All control numbers should be unique
        assert len(control_numbers) == len(set(control_numbers))
        
        # Get resident's document history
        docs = DocumentModel.get_resident_documents(sample_resident)
        assert len(docs) >= len(doc_types)
    
    def test_document_search(self, setup_database, sample_resident):
        """Test searching for documents."""
        # Issue a document with distinct purpose
        result = DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="UniqueSearchTerm123"
        )
        
        # Search by control number
        docs = DocumentModel.search(result['control_number'])
        assert len(docs) >= 1
    
    def test_document_statistics(self, setup_database, sample_resident):
        """Test document statistics are properly tracked."""
        # Issue a paid document
        DocumentModel.issue_document(
            res_id=sample_resident,
            doc_type="Clearance",
            purpose="Stats Test",
            amount=50.00,
            or_number="OR-STATS-001"
        )
        
        stats = DocumentModel.get_statistics()
        
        assert stats['total_issued'] > 0
        assert stats['total_revenue'] >= 50.00
        assert 'Clearance' in stats['by_type']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
