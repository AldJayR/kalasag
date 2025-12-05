"""
KALASAG - Resident Model
CRUD operations for Residents and Households.
Implements FR-1.1, FR-1.2, FR-1.3, FR-1.4
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, log_audit
from datetime import datetime
from typing import Optional, List, Dict, Any


class HouseholdModel:
    """Model for Household CRUD operations."""
    
    @staticmethod
    def create(house_number: str, street_name: str, purok_id: int = None) -> int:
        """
        Create a new household.
        
        Args:
            house_number: House/lot number
            street_name: Street name
            purok_id: Foreign key to purok table
            
        Returns:
            The new household ID (hh_id)
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO household (house_number, street_name, purok_id)
            VALUES (?, ?, ?)
        """, (house_number, street_name, purok_id))
        
        hh_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return hh_id
    
    @staticmethod
    def get_by_id(hh_id: int) -> Optional[Dict[str, Any]]:
        """Get a household by ID."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT h.*, p.purok_name
            FROM household h
            LEFT JOIN purok p ON h.purok_id = p.purok_id
            WHERE h.hh_id = ?
        """, (hh_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all households."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT h.*, p.purok_name,
                   (SELECT COUNT(*) FROM resident r WHERE r.hh_id = h.hh_id) as member_count
            FROM household h
            LEFT JOIN purok p ON h.purok_id = p.purok_id
            ORDER BY h.hh_id DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def update(hh_id: int, house_number: str = None, street_name: str = None, 
               purok_id: int = None) -> bool:
        """Update a household."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        updates = []
        params = []
        
        if house_number is not None:
            updates.append("house_number = ?")
            params.append(house_number)
        if street_name is not None:
            updates.append("street_name = ?")
            params.append(street_name)
        if purok_id is not None:
            updates.append("purok_id = ?")
            params.append(purok_id)
        
        if not updates:
            conn.close()
            return False
        
        params.append(hh_id)
        query = f"UPDATE household SET {', '.join(updates)} WHERE hh_id = ?"
        
        cursor.execute(query, params)
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    @staticmethod
    def delete(hh_id: int) -> bool:
        """Delete a household (only if no residents are linked)."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check for linked residents
        cursor.execute("SELECT COUNT(*) FROM resident WHERE hh_id = ?", (hh_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise ValueError("Cannot delete household with linked residents")
        
        cursor.execute("DELETE FROM household WHERE hh_id = ?", (hh_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    @staticmethod
    def get_members(hh_id: int) -> List[Dict[str, Any]]:
        """Get all residents in a household."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM resident WHERE hh_id = ? ORDER BY last_name, first_name
        """, (hh_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


class ResidentModel:
    """Model for Resident CRUD operations."""
    
    @staticmethod
    def create(first_name: str, last_name: str, middle_name: str = None,
               alias: str = None, birthdate: str = None, sex: str = None,
               civil_status: str = None, occupation: str = None,
               purok_id: int = None, hh_id: int = None, is_indigent: bool = False,
               status: str = "Active", photo_blob: bytes = None,
               contact_number: str = None, user_id: int = None) -> int:
        """
        Create a new resident profile (FR-1.1).
        
        Args:
            first_name: Resident's first name
            last_name: Resident's last name
            middle_name: Resident's middle name (optional)
            alias: Known alias/nickname (optional)
            birthdate: Date of birth in YYYY-MM-DD format
            sex: 'Male' or 'Female'
            civil_status: 'Single', 'Married', 'Widowed', 'Separated', 'Divorced'
            occupation: Resident's occupation
            purok_id: Foreign key to purok table
            hh_id: Foreign key to household table (FR-1.2)
            is_indigent: Whether resident is tagged as indigent (FR-1.4)
            status: 'Active', 'Deceased', or 'Moved Out' (FR-1.4)
            photo_blob: Photo as binary data
            contact_number: Contact phone number
            user_id: ID of user performing the action (for audit)
            
        Returns:
            The new resident ID (res_id)
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO resident (
                first_name, middle_name, last_name, alias, birthdate, sex,
                civil_status, occupation, purok_id, hh_id, is_indigent,
                status, photo_blob, contact_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            first_name, middle_name, last_name, alias, birthdate, sex,
            civil_status, occupation, purok_id, hh_id, 
            1 if is_indigent else 0, status, photo_blob, contact_number
        ))
        
        res_id = cursor.lastrowid
        conn.commit()
        
        # Log audit trail
        if user_id:
            log_audit(user_id, "CREATE", "resident", res_id, None, 
                     f"Created resident: {first_name} {last_name}")
        
        conn.close()
        return res_id
    
    @staticmethod
    def get_by_id(res_id: int) -> Optional[Dict[str, Any]]:
        """Get a resident by ID."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.*, p.purok_name, h.house_number, h.street_name
            FROM resident r
            LEFT JOIN purok p ON r.purok_id = p.purok_id
            LEFT JOIN household h ON r.hh_id = h.hh_id
            WHERE r.res_id = ?
        """, (res_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    @staticmethod
    def get_all(status: str = None, purok_id: int = None, 
                is_indigent: bool = None) -> List[Dict[str, Any]]:
        """
        Get all residents with optional filters.
        
        Args:
            status: Filter by status ('Active', 'Deceased', 'Moved Out')
            purok_id: Filter by purok
            is_indigent: Filter by indigent status
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT r.*, p.purok_name, h.house_number, h.street_name
            FROM resident r
            LEFT JOIN purok p ON r.purok_id = p.purok_id
            LEFT JOIN household h ON r.hh_id = h.hh_id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND r.status = ?"
            params.append(status)
        if purok_id:
            query += " AND r.purok_id = ?"
            params.append(purok_id)
        if is_indigent is not None:
            query += " AND r.is_indigent = ?"
            params.append(1 if is_indigent else 0)
        
        query += " ORDER BY r.last_name, r.first_name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def search(keyword: str, search_by: str = "name") -> List[Dict[str, Any]]:
        """
        Search residents by name, alias, or household ID (FR-1.3).
        
        Args:
            keyword: Search term
            search_by: 'name', 'alias', or 'household'
            
        Returns:
            List of matching residents
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        base_query = """
            SELECT r.*, p.purok_name, h.house_number, h.street_name
            FROM resident r
            LEFT JOIN purok p ON r.purok_id = p.purok_id
            LEFT JOIN household h ON r.hh_id = h.hh_id
            WHERE 
        """
        
        if search_by == "name":
            query = base_query + """
                (r.first_name LIKE ? OR r.last_name LIKE ? 
                 OR r.middle_name LIKE ? OR (r.first_name || ' ' || r.last_name) LIKE ?)
            """
            search_term = f"%{keyword}%"
            params = [search_term, search_term, search_term, search_term]
        
        elif search_by == "alias":
            query = base_query + "r.alias LIKE ?"
            params = [f"%{keyword}%"]
        
        elif search_by == "household":
            query = base_query + "r.hh_id = ?"
            try:
                params = [int(keyword)]
            except ValueError:
                conn.close()
                return []
        
        else:
            # Search all fields
            query = base_query + """
                (r.first_name LIKE ? OR r.last_name LIKE ? 
                 OR r.middle_name LIKE ? OR r.alias LIKE ?
                 OR CAST(r.hh_id AS TEXT) = ?)
            """
            search_term = f"%{keyword}%"
            params = [search_term, search_term, search_term, search_term, keyword]
        
        query += " ORDER BY r.last_name, r.first_name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def update(res_id: int, user_id: int = None, **kwargs) -> bool:
        """
        Update a resident's information.
        
        Args:
            res_id: Resident ID to update
            user_id: ID of user performing the action (for audit)
            **kwargs: Fields to update (first_name, last_name, status, etc.)
            
        Returns:
            True if update successful
        """
        # Valid fields that can be updated
        valid_fields = {
            'first_name', 'middle_name', 'last_name', 'alias', 'birthdate',
            'sex', 'civil_status', 'occupation', 'purok_id', 'hh_id',
            'is_indigent', 'status', 'photo_blob', 'contact_number'
        }
        
        # Filter out invalid fields
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get old values for audit
        old_data = None
        if user_id:
            cursor.execute("SELECT * FROM resident WHERE res_id = ?", (res_id,))
            row = cursor.fetchone()
            if row:
                old_data = dict(row)
        
        # Handle is_indigent conversion
        if 'is_indigent' in updates:
            updates['is_indigent'] = 1 if updates['is_indigent'] else 0
        
        # Add updated_at timestamp
        updates['updated_at'] = datetime.now().isoformat()
        
        # Build query
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        params = list(updates.values()) + [res_id]
        
        cursor.execute(f"UPDATE resident SET {set_clause} WHERE res_id = ?", params)
        affected = cursor.rowcount
        conn.commit()
        
        # Log audit trail
        if user_id and affected > 0:
            log_audit(user_id, "UPDATE", "resident", res_id, 
                     str(old_data), str(updates))
        
        conn.close()
        return affected > 0
    
    @staticmethod
    def update_status(res_id: int, status: str, user_id: int = None) -> bool:
        """
        Update resident status (FR-1.4).
        
        Args:
            res_id: Resident ID
            status: New status ('Active', 'Deceased', 'Moved Out')
            user_id: ID of user performing the action
        """
        if status not in ('Active', 'Deceased', 'Moved Out'):
            raise ValueError(f"Invalid status: {status}")
        
        return ResidentModel.update(res_id, user_id=user_id, status=status)
    
    @staticmethod
    def update_indigent_status(res_id: int, is_indigent: bool, 
                                user_id: int = None) -> bool:
        """
        Update resident indigent status (FR-1.4).
        
        Args:
            res_id: Resident ID
            is_indigent: True if indigent
            user_id: ID of user performing the action
        """
        return ResidentModel.update(res_id, user_id=user_id, is_indigent=is_indigent)
    
    @staticmethod
    def delete(res_id: int, user_id: int = None) -> bool:
        """
        Delete a resident (soft delete recommended, but this is hard delete).
        
        Note: Consider using update_status to 'Moved Out' instead.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check for linked blotter cases
        cursor.execute("""
            SELECT COUNT(*) FROM case_involvement WHERE res_id = ?
        """, (res_id,))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise ValueError("Cannot delete resident with linked blotter cases. "
                           "Consider changing status to 'Moved Out' instead.")
        
        # Get resident info for audit before deletion
        cursor.execute("SELECT first_name, last_name FROM resident WHERE res_id = ?", 
                      (res_id,))
        resident = cursor.fetchone()
        
        cursor.execute("DELETE FROM resident WHERE res_id = ?", (res_id,))
        affected = cursor.rowcount
        conn.commit()
        
        # Log audit trail
        if user_id and affected > 0 and resident:
            log_audit(user_id, "DELETE", "resident", res_id, 
                     f"{resident['first_name']} {resident['last_name']}", None)
        
        conn.close()
        return affected > 0
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """Get resident statistics for dashboard."""
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM resident 
            GROUP BY status
        """)
        stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total active residents
        stats['total_active'] = stats['by_status'].get('Active', 0)
        
        # Indigent count
        cursor.execute("""
            SELECT COUNT(*) FROM resident WHERE is_indigent = 1 AND status = 'Active'
        """)
        stats['indigent_count'] = cursor.fetchone()[0]
        
        # Count by purok
        cursor.execute("""
            SELECT p.purok_name, COUNT(r.res_id) as count
            FROM purok p
            LEFT JOIN resident r ON p.purok_id = r.purok_id AND r.status = 'Active'
            GROUP BY p.purok_id
            ORDER BY p.purok_name
        """)
        stats['by_purok'] = {row['purok_name']: row['count'] for row in cursor.fetchall()}
        
        # Count by sex
        cursor.execute("""
            SELECT sex, COUNT(*) as count 
            FROM resident 
            WHERE status = 'Active' AND sex IS NOT NULL
            GROUP BY sex
        """)
        stats['by_sex'] = {row['sex']: row['count'] for row in cursor.fetchall()}
        
        # Total households
        cursor.execute("SELECT COUNT(*) FROM household")
        stats['total_households'] = cursor.fetchone()[0]
        
        conn.close()
        return stats


class PurokModel:
    """Model for Purok operations."""
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all puroks."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, 
                   (SELECT COUNT(*) FROM resident r WHERE r.purok_id = p.purok_id AND r.status = 'Active') as resident_count
            FROM purok p
            ORDER BY p.purok_name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_id(purok_id: int) -> Optional[Dict[str, Any]]:
        """Get a purok by ID."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM purok WHERE purok_id = ?", (purok_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    @staticmethod
    def create(purok_name: str, assigned_tanod_leader: str = None) -> int:
        """Create a new purok."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO purok (purok_name, assigned_tanod_leader)
            VALUES (?, ?)
        """, (purok_name, assigned_tanod_leader))
        
        purok_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return purok_id
    
    @staticmethod
    def update(purok_id: int, purok_name: str = None, 
               assigned_tanod_leader: str = None) -> bool:
        """Update a purok."""
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if purok_name is not None:
            updates.append("purok_name = ?")
            params.append(purok_name)
        if assigned_tanod_leader is not None:
            updates.append("assigned_tanod_leader = ?")
            params.append(assigned_tanod_leader)
        
        if not updates:
            conn.close()
            return False
        
        params.append(purok_id)
        query = f"UPDATE purok SET {', '.join(updates)} WHERE purok_id = ?"
        
        cursor.execute(query, params)
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
