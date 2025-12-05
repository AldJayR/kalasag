"""
KALASAG - Blotter Model
CRUD operations for E-Blotter & Case Management.
Implements FR-2.1, FR-2.2, FR-2.3, FR-2.4
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, log_audit, generate_case_number, check_recidivist
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple


class IncidentTypeModel:
    """Model for Incident Type operations."""
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all incident types."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM incident_type ORDER BY severity DESC, name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_id(type_id: int) -> Optional[Dict[str, Any]]:
        """Get an incident type by ID."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM incident_type WHERE type_id = ?", (type_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    @staticmethod
    def create(name: str, severity: int, description: str = None) -> int:
        """Create a new incident type."""
        if severity < 1 or severity > 5:
            raise ValueError("Severity must be between 1 and 5")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO incident_type (name, severity, description)
            VALUES (?, ?, ?)
        """, (name, severity, description))
        
        type_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return type_id
    
    @staticmethod
    def update(type_id: int, name: str = None, severity: int = None,
               description: str = None) -> bool:
        """Update an incident type."""
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if severity is not None:
            if severity < 1 or severity > 5:
                conn.close()
                raise ValueError("Severity must be between 1 and 5")
            updates.append("severity = ?")
            params.append(severity)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if not updates:
            conn.close()
            return False
        
        params.append(type_id)
        query = f"UPDATE incident_type SET {', '.join(updates)} WHERE type_id = ?"
        
        cursor.execute(query, params)
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0


class BlotterCaseModel:
    """Model for Blotter Case CRUD operations."""
    
    @staticmethod
    def create(date_time: str, narrative: str, purok_id: int = None,
               type_id: int = None, recorded_by: int = None,
               complainants: List[int] = None, respondents: List[int] = None,
               witnesses: List[int] = None) -> Tuple[int, str]:
        """
        Create a new blotter case (FR-2.1).
        
        Args:
            date_time: Incident date/time in ISO format
            narrative: Detailed description of the incident
            purok_id: Location (FK to purok table)
            type_id: Incident type (FK to incident_type table)
            recorded_by: User ID who recorded this case
            complainants: List of resident IDs as complainants (FR-2.2)
            respondents: List of resident IDs as respondents (FR-2.2)
            witnesses: List of resident IDs as witnesses
            
        Returns:
            Tuple of (case_id, case_number)
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Generate unique case number
        case_number = generate_case_number()
        
        cursor.execute("""
            INSERT INTO blotter_case (case_number, date_time, narrative, purok_id, type_id, recorded_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (case_number, date_time, narrative, purok_id, type_id, recorded_by))
        
        case_id = cursor.lastrowid
        
        # Add case involvements (FR-2.2)
        if complainants:
            for res_id in complainants:
                cursor.execute("""
                    INSERT INTO case_involvement (case_id, res_id, role)
                    VALUES (?, ?, 'Complainant')
                """, (case_id, res_id))
        
        if respondents:
            for res_id in respondents:
                cursor.execute("""
                    INSERT INTO case_involvement (case_id, res_id, role)
                    VALUES (?, ?, 'Respondent')
                """, (case_id, res_id))
        
        if witnesses:
            for res_id in witnesses:
                cursor.execute("""
                    INSERT INTO case_involvement (case_id, res_id, role)
                    VALUES (?, ?, 'Witness')
                """, (case_id, res_id))
        
        conn.commit()
        
        # Log audit trail
        if recorded_by:
            log_audit(recorded_by, "CREATE", "blotter_case", case_id, None,
                     f"Created case: {case_number}")
        
        conn.close()
        return case_id, case_number
    
    @staticmethod
    def get_by_id(case_id: int) -> Optional[Dict[str, Any]]:
        """Get a blotter case by ID with all related data."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT bc.*, p.purok_name, it.name as incident_type_name, it.severity,
                   u.full_name as recorded_by_name
            FROM blotter_case bc
            LEFT JOIN purok p ON bc.purok_id = p.purok_id
            LEFT JOIN incident_type it ON bc.type_id = it.type_id
            LEFT JOIN user u ON bc.recorded_by = u.user_id
            WHERE bc.case_id = ?
        """, (case_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        case = dict(row)
        
        # Get involved persons
        cursor.execute("""
            SELECT ci.*, r.first_name, r.middle_name, r.last_name, r.alias
            FROM case_involvement ci
            JOIN resident r ON ci.res_id = r.res_id
            WHERE ci.case_id = ?
        """, (case_id,))
        
        involvements = cursor.fetchall()
        
        case['complainants'] = [dict(i) for i in involvements if i['role'] == 'Complainant']
        case['respondents'] = [dict(i) for i in involvements if i['role'] == 'Respondent']
        case['witnesses'] = [dict(i) for i in involvements if i['role'] == 'Witness']
        
        conn.close()
        return case
    
    @staticmethod
    def get_by_case_number(case_number: str) -> Optional[Dict[str, Any]]:
        """Get a blotter case by case number."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT case_id FROM blotter_case WHERE case_number = ?", (case_number,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return BlotterCaseModel.get_by_id(row['case_id'])
        return None
    
    @staticmethod
    def get_all(status: str = None, purok_id: int = None, type_id: int = None,
                start_date: str = None, end_date: str = None,
                limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all blotter cases with optional filters.
        
        Args:
            status: Filter by case status (FR-2.3)
            purok_id: Filter by location
            type_id: Filter by incident type
            start_date: Filter by date range start (YYYY-MM-DD)
            end_date: Filter by date range end (YYYY-MM-DD)
            limit: Maximum number of results
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT bc.*, p.purok_name, it.name as incident_type_name, it.severity
            FROM blotter_case bc
            LEFT JOIN purok p ON bc.purok_id = p.purok_id
            LEFT JOIN incident_type it ON bc.type_id = it.type_id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND bc.status = ?"
            params.append(status)
        if purok_id:
            query += " AND bc.purok_id = ?"
            params.append(purok_id)
        if type_id:
            query += " AND bc.type_id = ?"
            params.append(type_id)
        if start_date:
            query += " AND DATE(bc.date_time) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(bc.date_time) <= ?"
            params.append(end_date)
        
        query += " ORDER BY bc.date_time DESC"
        
        if limit:
            query += f" LIMIT {int(limit)}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def search(keyword: str) -> List[Dict[str, Any]]:
        """Search blotter cases by case number or narrative."""
        conn = get_connection()
        cursor = conn.cursor()
        
        search_term = f"%{keyword}%"
        
        cursor.execute("""
            SELECT bc.*, p.purok_name, it.name as incident_type_name
            FROM blotter_case bc
            LEFT JOIN purok p ON bc.purok_id = p.purok_id
            LEFT JOIN incident_type it ON bc.type_id = it.type_id
            WHERE bc.case_number LIKE ? OR bc.narrative LIKE ?
            ORDER BY bc.date_time DESC
        """, (search_term, search_term))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def update_status(case_id: int, status: str, user_id: int = None) -> bool:
        """
        Update case status (FR-2.3).
        
        Args:
            case_id: Case ID to update
            status: New status ('Pending', 'Amicable Settlement', 'Escalated to PNP', 'Closed')
            user_id: User making the change (for audit)
        """
        valid_statuses = ('Pending', 'Amicable Settlement', 'Escalated to PNP', 'Closed')
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get old status for audit
        cursor.execute("SELECT status, case_number FROM blotter_case WHERE case_id = ?", (case_id,))
        old_row = cursor.fetchone()
        old_status = old_row['status'] if old_row else None
        case_number = old_row['case_number'] if old_row else None
        
        cursor.execute("""
            UPDATE blotter_case 
            SET status = ?, updated_at = ?
            WHERE case_id = ?
        """, (status, datetime.now().isoformat(), case_id))
        
        affected = cursor.rowcount
        conn.commit()
        
        # Log audit trail
        if user_id and affected > 0:
            log_audit(user_id, "UPDATE_STATUS", "blotter_case", case_id,
                     f"Status: {old_status}", f"Status: {status} (Case: {case_number})")
        
        conn.close()
        return affected > 0
    
    @staticmethod
    def update(case_id: int, user_id: int = None, **kwargs) -> bool:
        """
        Update blotter case details.
        
        Args:
            case_id: Case ID to update
            user_id: User making the change
            **kwargs: Fields to update (narrative, purok_id, type_id, date_time)
        """
        valid_fields = {'narrative', 'purok_id', 'type_id', 'date_time'}
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        updates['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        params = list(updates.values()) + [case_id]
        
        cursor.execute(f"UPDATE blotter_case SET {set_clause} WHERE case_id = ?", params)
        affected = cursor.rowcount
        conn.commit()
        
        if user_id and affected > 0:
            log_audit(user_id, "UPDATE", "blotter_case", case_id, None, str(updates))
        
        conn.close()
        return affected > 0
    
    @staticmethod
    def delete(case_id: int, user_id: int = None) -> bool:
        """
        Delete a blotter case (cascades to case_involvement).
        
        Warning: This is a hard delete. Consider updating status to 'Closed' instead.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get case info for audit
        cursor.execute("SELECT case_number FROM blotter_case WHERE case_id = ?", (case_id,))
        row = cursor.fetchone()
        case_number = row['case_number'] if row else None
        
        cursor.execute("DELETE FROM blotter_case WHERE case_id = ?", (case_id,))
        affected = cursor.rowcount
        conn.commit()
        
        if user_id and affected > 0:
            log_audit(user_id, "DELETE", "blotter_case", case_id,
                     f"Deleted case: {case_number}", None)
        
        conn.close()
        return affected > 0
    
    @staticmethod
    def get_cases_by_resident(res_id: int, role: str = None) -> List[Dict[str, Any]]:
        """
        Get all cases involving a specific resident.
        
        Args:
            res_id: Resident ID
            role: Optional filter by role ('Complainant', 'Respondent', 'Witness')
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT bc.*, ci.role, p.purok_name, it.name as incident_type_name
            FROM blotter_case bc
            JOIN case_involvement ci ON bc.case_id = ci.case_id
            LEFT JOIN purok p ON bc.purok_id = p.purok_id
            LEFT JOIN incident_type it ON bc.type_id = it.type_id
            WHERE ci.res_id = ?
        """
        params = [res_id]
        
        if role:
            query += " AND ci.role = ?"
            params.append(role)
        
        query += " ORDER BY bc.date_time DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_statistics(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get blotter statistics for dashboard."""
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Date filter clause
        date_filter = ""
        params = []
        if start_date:
            date_filter += " AND DATE(date_time) >= ?"
            params.append(start_date)
        if end_date:
            date_filter += " AND DATE(date_time) <= ?"
            params.append(end_date)
        
        # Total cases by status
        cursor.execute(f"""
            SELECT status, COUNT(*) as count 
            FROM blotter_case 
            WHERE 1=1 {date_filter}
            GROUP BY status
        """, params)
        stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total cases
        cursor.execute(f"SELECT COUNT(*) FROM blotter_case WHERE 1=1 {date_filter}", params)
        stats['total_cases'] = cursor.fetchone()[0]
        
        # Cases by purok
        cursor.execute(f"""
            SELECT p.purok_name, COUNT(bc.case_id) as count
            FROM purok p
            LEFT JOIN blotter_case bc ON p.purok_id = bc.purok_id {date_filter.replace('AND', 'AND' if date_filter else '')}
            GROUP BY p.purok_id
            ORDER BY count DESC
        """, params)
        stats['by_purok'] = {row['purok_name']: row['count'] for row in cursor.fetchall()}
        
        # Cases by incident type
        cursor.execute(f"""
            SELECT it.name, COUNT(bc.case_id) as count
            FROM incident_type it
            LEFT JOIN blotter_case bc ON it.type_id = bc.type_id {date_filter.replace('AND', 'AND' if date_filter else '')}
            GROUP BY it.type_id
            ORDER BY count DESC
        """, params)
        stats['by_type'] = {row['name']: row['count'] for row in cursor.fetchall()}
        
        # Pending cases count
        stats['pending_count'] = stats['by_status'].get('Pending', 0)
        
        conn.close()
        return stats


class CaseInvolvementModel:
    """Model for managing case involvements (linking residents to cases)."""
    
    @staticmethod
    def add_involvement(case_id: int, res_id: int, role: str) -> int:
        """
        Add a resident to a case (FR-2.2).
        
        Args:
            case_id: Blotter case ID
            res_id: Resident ID
            role: 'Complainant', 'Respondent', or 'Witness'
        """
        if role not in ('Complainant', 'Respondent', 'Witness'):
            raise ValueError("Role must be 'Complainant', 'Respondent', or 'Witness'")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO case_involvement (case_id, res_id, role)
            VALUES (?, ?, ?)
        """, (case_id, res_id, role))
        
        link_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return link_id
    
    @staticmethod
    def remove_involvement(case_id: int, res_id: int, role: str = None) -> bool:
        """Remove a resident from a case."""
        conn = get_connection()
        cursor = conn.cursor()
        
        if role:
            cursor.execute("""
                DELETE FROM case_involvement 
                WHERE case_id = ? AND res_id = ? AND role = ?
            """, (case_id, res_id, role))
        else:
            cursor.execute("""
                DELETE FROM case_involvement 
                WHERE case_id = ? AND res_id = ?
            """, (case_id, res_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    @staticmethod
    def get_involvements(case_id: int) -> List[Dict[str, Any]]:
        """Get all involvements for a case."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ci.*, r.first_name, r.middle_name, r.last_name, r.alias
            FROM case_involvement ci
            JOIN resident r ON ci.res_id = r.res_id
            WHERE ci.case_id = ?
            ORDER BY ci.role, r.last_name
        """, (case_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def check_recidivist(res_id: int) -> Dict[str, Any]:
        """
        Check if a resident is a recidivist (FR-2.4).
        
        Returns:
            Dict with is_recidivist, prior_cases count, and case_numbers list
        """
        return check_recidivist(res_id)
