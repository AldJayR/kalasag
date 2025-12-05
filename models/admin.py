"""
KALASAG - Admin Model
System administration and audit log operations.
Implements FR-5.1, FR-5.2
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, log_audit, backup_database, export_to_csv
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List


class AuditLogModel:
    """Model for Audit Trail operations (FR-5.2)."""
    
    # Actions that should be logged
    TRACKED_ACTIONS = [
        'CREATE_USER', 'UPDATE_USER', 'UPDATE_PASSWORD', 'DELETE_USER', 'DEACTIVATE_USER',
        'CREATE_RESIDENT', 'UPDATE_RESIDENT', 'DELETE_RESIDENT',
        'CREATE_BLOTTER', 'UPDATE_BLOTTER', 'DELETE_BLOTTER', 'CLOSE_CASE',
        'ISSUE_DOCUMENT', 'UPDATE_PAYMENT',
        'LOGIN', 'LOGOUT', 'LOGIN_FAILED',
        'BACKUP_DATABASE', 'RESTORE_DATABASE', 'EXPORT_DATA'
    ]
    
    @staticmethod
    def get_all(
        user_id: int = None,
        action: str = None,
        table_name: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries with optional filters (FR-5.2).
        
        Args:
            user_id: Filter by user who performed action
            action: Filter by action type
            table_name: Filter by affected table
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
            limit: Maximum number of records to return
            
        Returns:
            List of audit log entries
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT al.*, u.username, u.full_name as user_full_name
            FROM audit_log al
            LEFT JOIN user u ON al.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND al.user_id = ?"
            params.append(user_id)
        if action:
            query += " AND al.action = ?"
            params.append(action)
        if table_name:
            query += " AND al.table_name = ?"
            params.append(table_name)
        if start_date:
            query += " AND DATE(al.timestamp) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(al.timestamp) <= ?"
            params.append(end_date)
        
        query += f" ORDER BY al.timestamp DESC LIMIT {int(limit)}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_record(table_name: str, record_id: int) -> List[Dict[str, Any]]:
        """Get all audit log entries for a specific record."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT al.*, u.username, u.full_name as user_full_name
            FROM audit_log al
            LEFT JOIN user u ON al.user_id = u.user_id
            WHERE al.table_name = ? AND al.record_id = ?
            ORDER BY al.timestamp DESC
        """, (table_name, record_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_user_activity(user_id: int, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent activity for a specific user."""
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        return AuditLogModel.get_all(user_id=user_id, start_date=start_date)
    
    @staticmethod
    def get_statistics(days_back: int = 30) -> Dict[str, Any]:
        """Get audit log statistics."""
        conn = get_connection()
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        # Total actions in period
        cursor.execute("""
            SELECT COUNT(*) as total FROM audit_log
            WHERE DATE(timestamp) >= ?
        """, (start_date,))
        total_actions = cursor.fetchone()['total']
        
        # Actions by type
        cursor.execute("""
            SELECT action, COUNT(*) as count
            FROM audit_log
            WHERE DATE(timestamp) >= ?
            GROUP BY action
            ORDER BY count DESC
        """, (start_date,))
        by_action = {row['action']: row['count'] for row in cursor.fetchall()}
        
        # Actions by user
        cursor.execute("""
            SELECT u.username, u.full_name, COUNT(*) as count
            FROM audit_log al
            JOIN user u ON al.user_id = u.user_id
            WHERE DATE(al.timestamp) >= ?
            GROUP BY al.user_id
            ORDER BY count DESC
        """, (start_date,))
        by_user = [
            {'username': row['username'], 'full_name': row['full_name'], 'count': row['count']}
            for row in cursor.fetchall()
        ]
        
        # Daily activity
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM audit_log
            WHERE DATE(timestamp) >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (start_date,))
        daily_activity = [
            {'date': row['date'], 'count': row['count']}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'period_days': days_back,
            'total_actions': total_actions,
            'by_action': by_action,
            'by_user': by_user,
            'daily_activity': daily_activity
        }
    
    @staticmethod
    def search(keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search audit logs by keyword in old/new values."""
        conn = get_connection()
        cursor = conn.cursor()
        
        search_term = f"%{keyword}%"
        
        cursor.execute("""
            SELECT al.*, u.username, u.full_name as user_full_name
            FROM audit_log al
            LEFT JOIN user u ON al.user_id = u.user_id
            WHERE al.old_values LIKE ? OR al.new_values LIKE ?
            ORDER BY al.timestamp DESC
            LIMIT ?
        """, (search_term, search_term, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


class SystemSettingsModel:
    """Model for system settings and configuration."""
    
    # Default settings
    DEFAULT_SETTINGS = {
        'barangay_name': 'Sample Barangay',
        'municipality': 'Sample Municipality',
        'province': 'Sample Province',
        'captain_name': 'Hon. Juan Dela Cruz',
        'captain_title': 'Punong Barangay',
        'backup_retention_days': 30,
        'session_timeout_minutes': 30,
        'auto_backup_enabled': True
    }
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get a system setting value."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if settings table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='system_settings'
        """)
        
        if not cursor.fetchone():
            conn.close()
            return SystemSettingsModel.DEFAULT_SETTINGS.get(key, default)
        
        cursor.execute("""
            SELECT value FROM system_settings WHERE key = ?
        """, (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return row['value']
        return SystemSettingsModel.DEFAULT_SETTINGS.get(key, default)
    
    @staticmethod
    def get_all() -> Dict[str, Any]:
        """Get all system settings."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Start with defaults
        settings = SystemSettingsModel.DEFAULT_SETTINGS.copy()
        
        # Check if settings table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='system_settings'
        """)
        
        if cursor.fetchone():
            cursor.execute("SELECT key, value FROM system_settings")
            for row in cursor.fetchall():
                settings[row['key']] = row['value']
        
        conn.close()
        return settings
    
    @staticmethod
    def set(key: str, value: Any, updated_by: int = None) -> bool:
        """Set a system setting value."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create settings table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Upsert the setting
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, str(value), datetime.now().isoformat()))
        
        conn.commit()
        
        if updated_by:
            log_audit(updated_by, "UPDATE_SETTING", "system_settings", None, 
                     None, f"{key}={value}")
        
        conn.close()
        return True


class BackupModel:
    """Model for database backup operations (FR-5.1)."""
    
    @staticmethod
    def create_backup(backup_path: str = None, user_id: int = None) -> str:
        """
        Create a database backup (FR-5.1).
        
        Args:
            backup_path: Optional custom path for backup
            user_id: User performing the backup
            
        Returns:
            Path to the backup file
        """
        path = backup_database(backup_path)
        
        if user_id:
            log_audit(user_id, "BACKUP_DATABASE", None, None, None, f"Backup: {path}")
        
        return path
    
    @staticmethod
    def export_table_csv(table_name: str, output_path: str = None, 
                         user_id: int = None) -> str:
        """
        Export a table to CSV format (FR-5.1).
        
        Args:
            table_name: Name of table to export
            output_path: Optional custom path for export
            user_id: User performing the export
            
        Returns:
            Path to the CSV file
        """
        # Validate table name to prevent SQL injection
        valid_tables = [
            'resident', 'household', 'purok', 'user', 
            'blotter_case', 'case_involvement', 'incident_type',
            'doc_log', 'audit_log'
        ]
        
        if table_name not in valid_tables:
            raise ValueError(f"Invalid table name. Valid tables: {valid_tables}")
        
        path = export_to_csv(table_name, output_path)
        
        if user_id:
            log_audit(user_id, "EXPORT_DATA", table_name, None, None, f"Export: {path}")
        
        return path
    
    @staticmethod
    def export_all_tables(output_dir: str = None, user_id: int = None) -> List[str]:
        """
        Export all tables to CSV files (FR-5.1).
        
        Returns:
            List of paths to exported CSV files
        """
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"export_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        tables = [
            'resident', 'household', 'purok', 'user',
            'blotter_case', 'case_involvement', 'incident_type',
            'doc_log', 'audit_log'
        ]
        
        exported_files = []
        for table in tables:
            try:
                output_path = os.path.join(output_dir, f"{table}.csv")
                path = export_to_csv(table, output_path)
                exported_files.append(path)
            except Exception as e:
                print(f"Warning: Failed to export {table}: {e}")
        
        if user_id:
            log_audit(user_id, "EXPORT_DATA", None, None, None, 
                     f"Exported {len(exported_files)} tables to {output_dir}")
        
        return exported_files
    
    @staticmethod
    def get_backup_history(backup_dir: str = ".") -> List[Dict[str, Any]]:
        """Get list of existing backup files."""
        backups = []
        
        for file in os.listdir(backup_dir):
            if file.startswith("backup_kalasag_") and file.endswith(".db"):
                filepath = os.path.join(backup_dir, file)
                stat = os.stat(filepath)
                backups.append({
                    'filename': file,
                    'path': filepath,
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sort by creation date, newest first
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
