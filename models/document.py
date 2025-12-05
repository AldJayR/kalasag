"""
KALASAG - Document Model
CRUD operations for Document Issuance.
Implements FR-3.1, FR-3.2, FR-3.3
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, log_audit, generate_control_number
from datetime import datetime
from typing import Optional, List, Dict, Any


class DocumentModel:
    """Model for Document issuance and logging operations."""
    
    VALID_DOC_TYPES = ('Clearance', 'Indigency', 'Permit', 'Residency', 'Business Permit')
    
    @staticmethod
    def issue_document(res_id: int, doc_type: str, purpose: str = None,
                       amount: float = 0, or_number: str = None,
                       issued_by: int = None) -> Dict[str, Any]:
        """
        Issue a new document and log it (FR-3.1, FR-3.2, FR-3.3).
        
        Args:
            res_id: Resident ID to issue document for
            doc_type: Type of document ('Clearance', 'Indigency', 'Permit', 'Residency', 'Business Permit')
            purpose: Purpose of the document
            amount: Amount paid (FR-3.3)
            or_number: Official Receipt number (FR-3.3)
            issued_by: User ID who issued this document
            
        Returns:
            Dict containing doc_id, control_number, and other details
        """
        if doc_type not in DocumentModel.VALID_DOC_TYPES:
            raise ValueError(f"Invalid document type. Must be one of: {DocumentModel.VALID_DOC_TYPES}")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify resident exists
        cursor.execute("SELECT res_id, status FROM resident WHERE res_id = ?", (res_id,))
        resident = cursor.fetchone()
        if not resident:
            conn.close()
            raise ValueError(f"Resident with ID {res_id} not found")
        
        # Check if indigency requires indigent status
        if doc_type == 'Indigency':
            cursor.execute("SELECT is_indigent FROM resident WHERE res_id = ?", (res_id,))
            row = cursor.fetchone()
            if not row or not row['is_indigent']:
                conn.close()
                raise ValueError("Certificate of Indigency can only be issued to residents tagged as indigent")
        
        # Generate unique control number (FR-3.2)
        control_number = generate_control_number(doc_type)
        
        cursor.execute("""
            INSERT INTO doc_log (control_number, res_id, doc_type, purpose, amount, or_number, issued_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (control_number, res_id, doc_type, purpose, amount, or_number, issued_by))
        
        doc_id = cursor.lastrowid
        conn.commit()
        
        # Log audit trail
        if issued_by:
            log_audit(issued_by, "ISSUE_DOCUMENT", "doc_log", doc_id, None,
                     f"Issued {doc_type}: {control_number}")
        
        conn.close()
        
        return {
            'doc_id': doc_id,
            'control_number': control_number,
            'doc_type': doc_type,
            'res_id': res_id,
            'purpose': purpose,
            'amount': amount,
            'or_number': or_number
        }
    
    @staticmethod
    def get_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
        """Get a document log entry by ID."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT dl.*, r.first_name, r.middle_name, r.last_name,
                   r.birthdate, r.sex, r.civil_status, r.occupation,
                   p.purok_name, h.house_number, h.street_name,
                   u.full_name as issued_by_name
            FROM doc_log dl
            JOIN resident r ON dl.res_id = r.res_id
            LEFT JOIN purok p ON r.purok_id = p.purok_id
            LEFT JOIN household h ON r.hh_id = h.hh_id
            LEFT JOIN user u ON dl.issued_by = u.user_id
            WHERE dl.doc_id = ?
        """, (doc_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    @staticmethod
    def get_by_control_number(control_number: str) -> Optional[Dict[str, Any]]:
        """Get a document log entry by control number."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT doc_id FROM doc_log WHERE control_number = ?", (control_number,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return DocumentModel.get_by_id(row['doc_id'])
        return None
    
    @staticmethod
    def get_all(doc_type: str = None, res_id: int = None,
                start_date: str = None, end_date: str = None,
                limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all document logs with optional filters.
        
        Args:
            doc_type: Filter by document type
            res_id: Filter by resident
            start_date: Filter by date range start
            end_date: Filter by date range end
            limit: Maximum number of results
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT dl.*, r.first_name, r.middle_name, r.last_name,
                   u.full_name as issued_by_name
            FROM doc_log dl
            JOIN resident r ON dl.res_id = r.res_id
            LEFT JOIN user u ON dl.issued_by = u.user_id
            WHERE 1=1
        """
        params = []
        
        if doc_type:
            query += " AND dl.doc_type = ?"
            params.append(doc_type)
        if res_id:
            query += " AND dl.res_id = ?"
            params.append(res_id)
        if start_date:
            query += " AND DATE(dl.issued_at) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(dl.issued_at) <= ?"
            params.append(end_date)
        
        query += " ORDER BY dl.issued_at DESC"
        
        if limit:
            query += f" LIMIT {int(limit)}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_resident_documents(res_id: int) -> List[Dict[str, Any]]:
        """Get all documents issued to a specific resident."""
        return DocumentModel.get_all(res_id=res_id)
    
    @staticmethod
    def search(keyword: str) -> List[Dict[str, Any]]:
        """Search documents by control number, resident name, or OR number."""
        conn = get_connection()
        cursor = conn.cursor()
        
        search_term = f"%{keyword}%"
        
        cursor.execute("""
            SELECT dl.*, r.first_name, r.middle_name, r.last_name,
                   u.full_name as issued_by_name
            FROM doc_log dl
            JOIN resident r ON dl.res_id = r.res_id
            LEFT JOIN user u ON dl.issued_by = u.user_id
            WHERE dl.control_number LIKE ? 
               OR dl.or_number LIKE ?
               OR r.first_name LIKE ?
               OR r.last_name LIKE ?
               OR (r.first_name || ' ' || r.last_name) LIKE ?
            ORDER BY dl.issued_at DESC
        """, (search_term, search_term, search_term, search_term, search_term))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def verify_control_number(control_number: str) -> Dict[str, Any]:
        """
        Verify a control number is valid and get document details.
        Used to check document authenticity.
        """
        doc = DocumentModel.get_by_control_number(control_number)
        
        if doc:
            return {
                'valid': True,
                'document': doc,
                'message': f"Valid {doc['doc_type']} issued on {doc['issued_at']}"
            }
        else:
            return {
                'valid': False,
                'document': None,
                'message': "Control number not found in records"
            }
    
    @staticmethod
    def get_statistics(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get document issuance statistics."""
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Date filter clause
        date_filter = ""
        params = []
        if start_date:
            date_filter += " AND DATE(issued_at) >= ?"
            params.append(start_date)
        if end_date:
            date_filter += " AND DATE(issued_at) <= ?"
            params.append(end_date)
        
        # Total by document type
        cursor.execute(f"""
            SELECT doc_type, COUNT(*) as count, SUM(amount) as total_amount
            FROM doc_log
            WHERE 1=1 {date_filter}
            GROUP BY doc_type
        """, params)
        
        by_type = {}
        total_revenue = 0
        for row in cursor.fetchall():
            by_type[row['doc_type']] = {
                'count': row['count'],
                'revenue': row['total_amount'] or 0
            }
            total_revenue += row['total_amount'] or 0
        
        stats['by_type'] = by_type
        stats['total_revenue'] = total_revenue
        
        # Total documents issued
        cursor.execute(f"SELECT COUNT(*) FROM doc_log WHERE 1=1 {date_filter}", params)
        stats['total_issued'] = cursor.fetchone()[0]
        
        # Today's issuances
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT COUNT(*) FROM doc_log WHERE DATE(issued_at) = ?
        """, (today,))
        stats['issued_today'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    @staticmethod
    def update_payment(doc_id: int, amount: float, or_number: str,
                       updated_by: int = None) -> bool:
        """
        Update payment details for a document (FR-3.3).
        Used when payment is made after document request.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE doc_log SET amount = ?, or_number = ?
            WHERE doc_id = ?
        """, (amount, or_number, doc_id))
        
        affected = cursor.rowcount
        conn.commit()
        
        if updated_by and affected > 0:
            log_audit(updated_by, "UPDATE_PAYMENT", "doc_log", doc_id, None,
                     f"Amount: {amount}, OR#: {or_number}")
        
        conn.close()
        return affected > 0
