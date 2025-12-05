"""
KALASAG - PDF Generator
ReportLab PDF templates for document generation.
Implements FR-3.1
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import Dict, Any, Optional
import os


# Base directory for assets
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')


def get_styles():
    """Get custom paragraph styles for documents."""
    styles = getSampleStyleSheet()
    
    # Header style (Barangay name)
    styles.add(ParagraphStyle(
        name='DocHeader',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))
    
    # Subheader style
    styles.add(ParagraphStyle(
        name='DocSubHeader',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=12
    ))
    
    # Title style (Document type)
    styles.add(ParagraphStyle(
        name='DocTitle',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceBefore=20,
        spaceAfter=20,
        fontName='Helvetica-Bold',
        underline=True
    ))
    
    # Body text style
    styles.add(ParagraphStyle(
        name='DocBody',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceBefore=6,
        spaceAfter=6,
        leading=16,
        firstLineIndent=36
    ))
    
    # Bold body text
    styles.add(ParagraphStyle(
        name='DocBodyBold',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    ))
    
    # Control number style
    styles.add(ParagraphStyle(
        name='ControlNumber',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        textColor=colors.darkgray
    ))
    
    # Signature style
    styles.add(ParagraphStyle(
        name='Signature',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceBefore=40
    ))
    
    return styles


def format_date_long(date_str: str = None) -> str:
    """Format date as 'December 5, 2025'."""
    if date_str:
        try:
            date = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        except ValueError:
            date = datetime.now()
    else:
        date = datetime.now()
    
    return date.strftime("%B %d, %Y")


def calculate_age(birthdate: str) -> Optional[int]:
    """Calculate age from birthdate."""
    if not birthdate:
        return None
    try:
        birth = datetime.strptime(str(birthdate)[:10], "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        return age
    except ValueError:
        return None


def format_address(doc_data: Dict[str, Any]) -> str:
    """Format full address from document data."""
    parts = []
    if doc_data.get('house_number'):
        parts.append(f"#{doc_data['house_number']}")
    if doc_data.get('street_name'):
        parts.append(doc_data['street_name'])
    if doc_data.get('purok_name'):
        parts.append(doc_data['purok_name'])
    
    return ", ".join(parts) if parts else "Barangay [Name]"


def format_name(doc_data: Dict[str, Any]) -> str:
    """Format full name from document data."""
    parts = [doc_data.get('first_name', '')]
    if doc_data.get('middle_name'):
        parts.append(doc_data['middle_name'])
    parts.append(doc_data.get('last_name', ''))
    return " ".join(p for p in parts if p)


class PDFGenerator:
    """Generate PDF documents for barangay issuances."""
    
    # Barangay information (can be configured)
    BARANGAY_NAME = "BARANGAY [NAME]"
    MUNICIPALITY = "Municipality of [Name]"
    PROVINCE = "Province of [Name]"
    CAPTAIN_NAME = "[Barangay Captain Name]"
    CAPTAIN_TITLE = "Punong Barangay"
    
    @staticmethod
    def generate_clearance(doc_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate Barangay Clearance PDF (FR-3.1).
        
        Args:
            doc_data: Document data from DocumentModel.get_by_id()
            output_path: Path to save the PDF
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = get_styles()
        story = []
        
        # Header
        story.append(Paragraph("Republic of the Philippines", styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.PROVINCE, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.MUNICIPALITY, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.BARANGAY_NAME, styles['DocHeader']))
        story.append(Spacer(1, 12))
        
        # Control Number
        story.append(Paragraph(
            f"Control No.: <b>{doc_data.get('control_number', 'N/A')}</b>",
            styles['ControlNumber']
        ))
        story.append(Spacer(1, 12))
        
        # Title
        story.append(Paragraph("BARANGAY CLEARANCE", styles['DocTitle']))
        story.append(Spacer(1, 20))
        
        # Salutation
        story.append(Paragraph("TO WHOM IT MAY CONCERN:", styles['DocBodyBold']))
        story.append(Spacer(1, 12))
        
        # Body
        full_name = format_name(doc_data)
        age = calculate_age(doc_data.get('birthdate'))
        age_text = f", {age} years old" if age else ""
        civil_status = doc_data.get('civil_status', '')
        civil_text = f", {civil_status.lower()}" if civil_status else ""
        address = format_address(doc_data)
        purpose = doc_data.get('purpose', 'whatever legal purpose it may serve')
        
        body_text = f"""This is to certify that <b>{full_name.upper()}</b>{age_text}{civil_text}, 
        is a bonafide resident of {address}, {PDFGenerator.BARANGAY_NAME}, {PDFGenerator.MUNICIPALITY}, 
        {PDFGenerator.PROVINCE}."""
        
        story.append(Paragraph(body_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Record verification
        record_text = """This is to certify further that the above-named person has no 
        derogatory record on file in this Barangay as of this date."""
        story.append(Paragraph(record_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Purpose
        purpose_text = f"""This certification is being issued upon the request of the 
        above-named person for <b>{purpose.upper()}</b>."""
        story.append(Paragraph(purpose_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Date issued
        date_issued = format_date_long(doc_data.get('issued_at'))
        story.append(Paragraph(
            f"Issued this <b>{date_issued}</b> at {PDFGenerator.BARANGAY_NAME}, "
            f"{PDFGenerator.MUNICIPALITY}, {PDFGenerator.PROVINCE}.",
            styles['DocBody']
        ))
        
        # Signature block
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"<b>{PDFGenerator.CAPTAIN_NAME}</b>", styles['Signature']))
        story.append(Paragraph(PDFGenerator.CAPTAIN_TITLE, styles['Signature']))
        
        # Footer with OR info
        if doc_data.get('or_number') or doc_data.get('amount'):
            story.append(Spacer(1, 40))
            or_text = []
            if doc_data.get('or_number'):
                or_text.append(f"O.R. No.: {doc_data['or_number']}")
            if doc_data.get('amount'):
                or_text.append(f"Amount Paid: ₱{doc_data['amount']:.2f}")
            story.append(Paragraph(" | ".join(or_text), styles['ControlNumber']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    @staticmethod
    def generate_indigency(doc_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate Certificate of Indigency PDF (FR-3.1).
        
        Args:
            doc_data: Document data from DocumentModel.get_by_id()
            output_path: Path to save the PDF
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = get_styles()
        story = []
        
        # Header
        story.append(Paragraph("Republic of the Philippines", styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.PROVINCE, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.MUNICIPALITY, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.BARANGAY_NAME, styles['DocHeader']))
        story.append(Spacer(1, 12))
        
        # Control Number
        story.append(Paragraph(
            f"Control No.: <b>{doc_data.get('control_number', 'N/A')}</b>",
            styles['ControlNumber']
        ))
        story.append(Spacer(1, 12))
        
        # Title
        story.append(Paragraph("CERTIFICATE OF INDIGENCY", styles['DocTitle']))
        story.append(Spacer(1, 20))
        
        # Salutation
        story.append(Paragraph("TO WHOM IT MAY CONCERN:", styles['DocBodyBold']))
        story.append(Spacer(1, 12))
        
        # Body
        full_name = format_name(doc_data)
        age = calculate_age(doc_data.get('birthdate'))
        age_text = f", {age} years old" if age else ""
        civil_status = doc_data.get('civil_status', '')
        civil_text = f", {civil_status.lower()}" if civil_status else ""
        address = format_address(doc_data)
        purpose = doc_data.get('purpose', 'financial/medical assistance')
        
        body_text = f"""This is to certify that <b>{full_name.upper()}</b>{age_text}{civil_text}, 
        is a bonafide resident of {address}, {PDFGenerator.BARANGAY_NAME}, {PDFGenerator.MUNICIPALITY}, 
        {PDFGenerator.PROVINCE}."""
        
        story.append(Paragraph(body_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Indigency statement
        indigency_text = """This is to certify further that the above-named person belongs to an 
        <b>INDIGENT FAMILY</b> in this Barangay, whose income is below the poverty threshold 
        and insufficient to meet the basic needs of the family."""
        story.append(Paragraph(indigency_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Purpose
        purpose_text = f"""This certification is being issued upon the request of the 
        above-named person in support of his/her application for <b>{purpose.upper()}</b>."""
        story.append(Paragraph(purpose_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Date issued
        date_issued = format_date_long(doc_data.get('issued_at'))
        story.append(Paragraph(
            f"Issued this <b>{date_issued}</b> at {PDFGenerator.BARANGAY_NAME}, "
            f"{PDFGenerator.MUNICIPALITY}, {PDFGenerator.PROVINCE}.",
            styles['DocBody']
        ))
        
        # Signature block
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"<b>{PDFGenerator.CAPTAIN_NAME}</b>", styles['Signature']))
        story.append(Paragraph(PDFGenerator.CAPTAIN_TITLE, styles['Signature']))
        
        # Footer
        story.append(Spacer(1, 40))
        story.append(Paragraph("NOT VALID WITHOUT OFFICIAL SEAL", styles['ControlNumber']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    @staticmethod
    def generate_residency(doc_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate Certificate of Residency PDF (FR-3.1).
        
        Args:
            doc_data: Document data from DocumentModel.get_by_id()
            output_path: Path to save the PDF
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = get_styles()
        story = []
        
        # Header
        story.append(Paragraph("Republic of the Philippines", styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.PROVINCE, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.MUNICIPALITY, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.BARANGAY_NAME, styles['DocHeader']))
        story.append(Spacer(1, 12))
        
        # Control Number
        story.append(Paragraph(
            f"Control No.: <b>{doc_data.get('control_number', 'N/A')}</b>",
            styles['ControlNumber']
        ))
        story.append(Spacer(1, 12))
        
        # Title
        story.append(Paragraph("CERTIFICATE OF RESIDENCY", styles['DocTitle']))
        story.append(Spacer(1, 20))
        
        # Salutation
        story.append(Paragraph("TO WHOM IT MAY CONCERN:", styles['DocBodyBold']))
        story.append(Spacer(1, 12))
        
        # Body
        full_name = format_name(doc_data)
        age = calculate_age(doc_data.get('birthdate'))
        age_text = f", {age} years old" if age else ""
        civil_status = doc_data.get('civil_status', '')
        civil_text = f", {civil_status.lower()}" if civil_status else ""
        address = format_address(doc_data)
        purpose = doc_data.get('purpose', 'whatever legal purpose it may serve')
        
        body_text = f"""This is to certify that <b>{full_name.upper()}</b>{age_text}{civil_text}, 
        is a bonafide and actual resident of {address}, {PDFGenerator.BARANGAY_NAME}, 
        {PDFGenerator.MUNICIPALITY}, {PDFGenerator.PROVINCE}."""
        
        story.append(Paragraph(body_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Duration statement
        duration_text = """Based on the records of this Barangay, the above-named person 
        has been residing in this Barangay for a considerable period of time."""
        story.append(Paragraph(duration_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Purpose
        purpose_text = f"""This certification is being issued upon the request of the 
        above-named person for <b>{purpose.upper()}</b>."""
        story.append(Paragraph(purpose_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Date issued
        date_issued = format_date_long(doc_data.get('issued_at'))
        story.append(Paragraph(
            f"Issued this <b>{date_issued}</b> at {PDFGenerator.BARANGAY_NAME}, "
            f"{PDFGenerator.MUNICIPALITY}, {PDFGenerator.PROVINCE}.",
            styles['DocBody']
        ))
        
        # Signature block
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"<b>{PDFGenerator.CAPTAIN_NAME}</b>", styles['Signature']))
        story.append(Paragraph(PDFGenerator.CAPTAIN_TITLE, styles['Signature']))
        
        # Footer with OR info
        if doc_data.get('or_number') or doc_data.get('amount'):
            story.append(Spacer(1, 40))
            or_text = []
            if doc_data.get('or_number'):
                or_text.append(f"O.R. No.: {doc_data['or_number']}")
            if doc_data.get('amount'):
                or_text.append(f"Amount Paid: ₱{doc_data['amount']:.2f}")
            story.append(Paragraph(" | ".join(or_text), styles['ControlNumber']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    @staticmethod
    def generate_permit(doc_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate Barangay Permit PDF (FR-3.1).
        
        Args:
            doc_data: Document data from DocumentModel.get_by_id()
            output_path: Path to save the PDF
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = get_styles()
        story = []
        
        # Header
        story.append(Paragraph("Republic of the Philippines", styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.PROVINCE, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.MUNICIPALITY, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.BARANGAY_NAME, styles['DocHeader']))
        story.append(Spacer(1, 12))
        
        # Control Number
        story.append(Paragraph(
            f"Control No.: <b>{doc_data.get('control_number', 'N/A')}</b>",
            styles['ControlNumber']
        ))
        story.append(Spacer(1, 12))
        
        # Title
        story.append(Paragraph("BARANGAY PERMIT", styles['DocTitle']))
        story.append(Spacer(1, 20))
        
        # Salutation
        story.append(Paragraph("TO WHOM IT MAY CONCERN:", styles['DocBodyBold']))
        story.append(Spacer(1, 12))
        
        # Body
        full_name = format_name(doc_data)
        address = format_address(doc_data)
        purpose = doc_data.get('purpose', 'conduct business/activity')
        
        body_text = f"""This is to certify that <b>{full_name.upper()}</b>, 
        a resident of {address}, {PDFGenerator.BARANGAY_NAME}, {PDFGenerator.MUNICIPALITY}, 
        {PDFGenerator.PROVINCE}, is hereby granted permission to <b>{purpose.upper()}</b> 
        within the jurisdiction of this Barangay."""
        
        story.append(Paragraph(body_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Conditions
        conditions_text = """This permit is issued subject to the following conditions:
        <br/>1. The holder shall comply with all Barangay ordinances and regulations.
        <br/>2. This permit may be revoked for violation of any rule or regulation.
        <br/>3. This permit is non-transferable."""
        story.append(Paragraph(conditions_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Date issued
        date_issued = format_date_long(doc_data.get('issued_at'))
        story.append(Paragraph(
            f"Issued this <b>{date_issued}</b> at {PDFGenerator.BARANGAY_NAME}, "
            f"{PDFGenerator.MUNICIPALITY}, {PDFGenerator.PROVINCE}.",
            styles['DocBody']
        ))
        
        # Signature block
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"<b>{PDFGenerator.CAPTAIN_NAME}</b>", styles['Signature']))
        story.append(Paragraph(PDFGenerator.CAPTAIN_TITLE, styles['Signature']))
        
        # Footer with OR info
        if doc_data.get('or_number') or doc_data.get('amount'):
            story.append(Spacer(1, 40))
            or_text = []
            if doc_data.get('or_number'):
                or_text.append(f"O.R. No.: {doc_data['or_number']}")
            if doc_data.get('amount'):
                or_text.append(f"Amount Paid: ₱{doc_data['amount']:.2f}")
            story.append(Paragraph(" | ".join(or_text), styles['ControlNumber']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    @staticmethod
    def generate_business_permit(doc_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate Barangay Business Permit PDF (FR-3.1).
        
        Args:
            doc_data: Document data from DocumentModel.get_by_id()
            output_path: Path to save the PDF
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = get_styles()
        story = []
        
        # Header
        story.append(Paragraph("Republic of the Philippines", styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.PROVINCE, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.MUNICIPALITY, styles['DocSubHeader']))
        story.append(Paragraph(PDFGenerator.BARANGAY_NAME, styles['DocHeader']))
        story.append(Spacer(1, 12))
        
        # Control Number
        story.append(Paragraph(
            f"Control No.: <b>{doc_data.get('control_number', 'N/A')}</b>",
            styles['ControlNumber']
        ))
        story.append(Spacer(1, 12))
        
        # Title
        story.append(Paragraph("BARANGAY BUSINESS CLEARANCE", styles['DocTitle']))
        story.append(Spacer(1, 20))
        
        # Salutation
        story.append(Paragraph("TO WHOM IT MAY CONCERN:", styles['DocBodyBold']))
        story.append(Spacer(1, 12))
        
        # Body
        full_name = format_name(doc_data)
        address = format_address(doc_data)
        purpose = doc_data.get('purpose', 'operate a business establishment')
        
        body_text = f"""This is to certify that <b>{full_name.upper()}</b>, 
        with business address at {address}, {PDFGenerator.BARANGAY_NAME}, {PDFGenerator.MUNICIPALITY}, 
        {PDFGenerator.PROVINCE}, has been granted clearance to <b>{purpose.upper()}</b>."""
        
        story.append(Paragraph(body_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Verification statement
        verification_text = """This is to certify further that per verification made, 
        the said business establishment has no pending complaint or case filed 
        against it in this Barangay."""
        story.append(Paragraph(verification_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Purpose
        purpose_text = """This clearance is being issued in connection with the 
        application for Business/Mayor's Permit with the Municipal/City Government."""
        story.append(Paragraph(purpose_text, styles['DocBody']))
        story.append(Spacer(1, 12))
        
        # Date issued
        date_issued = format_date_long(doc_data.get('issued_at'))
        story.append(Paragraph(
            f"Issued this <b>{date_issued}</b> at {PDFGenerator.BARANGAY_NAME}, "
            f"{PDFGenerator.MUNICIPALITY}, {PDFGenerator.PROVINCE}.",
            styles['DocBody']
        ))
        
        # Signature block
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"<b>{PDFGenerator.CAPTAIN_NAME}</b>", styles['Signature']))
        story.append(Paragraph(PDFGenerator.CAPTAIN_TITLE, styles['Signature']))
        
        # Footer with OR info
        if doc_data.get('or_number') or doc_data.get('amount'):
            story.append(Spacer(1, 40))
            or_text = []
            if doc_data.get('or_number'):
                or_text.append(f"O.R. No.: {doc_data['or_number']}")
            if doc_data.get('amount'):
                or_text.append(f"Amount Paid: ₱{doc_data['amount']:.2f}")
            story.append(Paragraph(" | ".join(or_text), styles['ControlNumber']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    @staticmethod
    def generate_document(doc_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate PDF based on document type.
        
        Args:
            doc_data: Document data from DocumentModel.get_by_id()
            output_path: Path to save the PDF
            
        Returns:
            Path to generated PDF
        """
        doc_type = doc_data.get('doc_type', 'Clearance')
        
        generators = {
            'Clearance': PDFGenerator.generate_clearance,
            'Indigency': PDFGenerator.generate_indigency,
            'Permit': PDFGenerator.generate_permit,
            'Residency': PDFGenerator.generate_residency,
            'Business Permit': PDFGenerator.generate_business_permit
        }
        
        generator = generators.get(doc_type, PDFGenerator.generate_clearance)
        return generator(doc_data, output_path)
