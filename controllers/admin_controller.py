"""
KALASAG - Admin Controller
Business logic for System Administration module.
Implements FR-5.1, FR-5.2
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from models.admin import AuditLogModel, SystemSettingsModel, BackupModel
from models.user import UserModel


class AdminController:
    """Controller for system administration operations."""
    
    # Minimum password length
    MIN_PASSWORD_LENGTH = 6
    
    # Valid user roles
    VALID_ROLES = ['Captain', 'Secretary', 'Tanod', 'Admin']
    
    # ==========================================
    # USER MANAGEMENT
    # ==========================================
    
    @staticmethod
    def create_user(
        username: str,
        password: str,
        full_name: str,
        role: str,
        created_by: int = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new user account.
        
        Returns:
            Tuple of (success, message, user_data)
        """
        # Validate inputs
        errors = []
        
        if not username or len(username.strip()) < 3:
            errors.append("Username must be at least 3 characters")
        
        if not password or len(password) < AdminController.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {AdminController.MIN_PASSWORD_LENGTH} characters")
        
        if not full_name or len(full_name.strip()) < 2:
            errors.append("Full name is required")
        
        if role not in AdminController.VALID_ROLES:
            errors.append(f"Invalid role. Valid roles: {', '.join(AdminController.VALID_ROLES)}")
        
        if errors:
            return False, "; ".join(errors), None
        
        try:
            user_id = UserModel.create(
                username=username.strip().lower(),
                password=password,
                full_name=full_name.strip(),
                role=role,
                created_by=created_by
            )
            
            user = UserModel.get_by_id(user_id)
            return True, f"User '{username}' created successfully", user
            
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Error creating user: {str(e)}", None
    
    @staticmethod
    def update_user(
        user_id: int,
        full_name: str = None,
        role: str = None,
        is_active: bool = None,
        updated_by: int = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update user information.
        
        Returns:
            Tuple of (success, message, updated_user)
        """
        # Verify user exists
        user = UserModel.get_by_id(user_id)
        if not user:
            return False, "User not found", None
        
        # Validate role if provided
        if role and role not in AdminController.VALID_ROLES:
            return False, f"Invalid role. Valid roles: {', '.join(AdminController.VALID_ROLES)}", None
        
        try:
            success = UserModel.update(
                user_id=user_id,
                full_name=full_name,
                role=role,
                is_active=is_active,
                updated_by=updated_by
            )
            
            if success:
                updated_user = UserModel.get_by_id(user_id)
                return True, "User updated successfully", updated_user
            else:
                return False, "No changes made", user
                
        except Exception as e:
            return False, f"Error updating user: {str(e)}", None
    
    @staticmethod
    def change_password(
        user_id: int,
        new_password: str,
        current_password: str = None,
        changed_by: int = None
    ) -> Tuple[bool, str]:
        """
        Change a user's password.
        
        Args:
            user_id: User whose password to change
            new_password: New password
            current_password: Current password (required for self-change)
            changed_by: User performing the change
            
        Returns:
            Tuple of (success, message)
        """
        # Verify user exists
        user = UserModel.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # If user is changing their own password, verify current password
        if changed_by == user_id and current_password:
            if not UserModel.verify_password(user_id, current_password):
                return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < AdminController.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {AdminController.MIN_PASSWORD_LENGTH} characters"
        
        try:
            success = UserModel.update_password(user_id, new_password, changed_by)
            
            if success:
                return True, "Password changed successfully"
            else:
                return False, "Failed to change password"
                
        except Exception as e:
            return False, f"Error changing password: {str(e)}"
    
    @staticmethod
    def deactivate_user(user_id: int, deactivated_by: int = None) -> Tuple[bool, str]:
        """
        Deactivate a user account.
        
        Returns:
            Tuple of (success, message)
        """
        user = UserModel.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        if not user['is_active']:
            return False, "User is already inactive"
        
        # Prevent deactivating yourself
        if deactivated_by == user_id:
            return False, "Cannot deactivate your own account"
        
        try:
            success = UserModel.deactivate(user_id, deactivated_by)
            
            if success:
                return True, f"User '{user['username']}' has been deactivated"
            else:
                return False, "Failed to deactivate user"
                
        except Exception as e:
            return False, f"Error deactivating user: {str(e)}"
    
    @staticmethod
    def get_all_users(include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all user accounts."""
        return UserModel.get_all(include_inactive=include_inactive)
    
    @staticmethod
    def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        return UserModel.get_by_id(user_id)
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate a user for login.
        
        Returns:
            Tuple of (success, message, user_data)
        """
        if not username or not password:
            return False, "Username and password are required", None
        
        user = UserModel.authenticate(username.strip().lower(), password)
        
        if user:
            return True, f"Welcome, {user['full_name']}", user
        else:
            return False, "Invalid username or password", None
    
    # ==========================================
    # BACKUP & RESTORE (FR-5.1)
    # ==========================================
    
    @staticmethod
    def create_backup(user_id: int = None) -> Tuple[bool, str, Optional[str]]:
        """
        Create a database backup (FR-5.1).
        
        Returns:
            Tuple of (success, message, backup_path)
        """
        try:
            backup_path = BackupModel.create_backup(user_id=user_id)
            return True, f"Backup created successfully", backup_path
        except Exception as e:
            return False, f"Backup failed: {str(e)}", None
    
    @staticmethod
    def export_to_csv(
        table_name: str = None,
        output_dir: str = None,
        user_id: int = None
    ) -> Tuple[bool, str, Optional[List[str]]]:
        """
        Export data to CSV files (FR-5.1).
        
        Args:
            table_name: Specific table to export, or None for all tables
            output_dir: Directory for output files
            user_id: User performing the export
            
        Returns:
            Tuple of (success, message, list_of_files)
        """
        try:
            if table_name:
                # Export single table
                path = BackupModel.export_table_csv(table_name, user_id=user_id)
                return True, f"Table '{table_name}' exported successfully", [path]
            else:
                # Export all tables
                files = BackupModel.export_all_tables(output_dir, user_id=user_id)
                return True, f"Exported {len(files)} tables successfully", files
                
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Export failed: {str(e)}", None
    
    @staticmethod
    def get_backup_list() -> List[Dict[str, Any]]:
        """Get list of available backups."""
        return BackupModel.get_backup_history()
    
    # ==========================================
    # AUDIT TRAIL (FR-5.2)
    # ==========================================
    
    @staticmethod
    def get_audit_logs(
        user_id: int = None,
        action: str = None,
        table_name: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get audit log entries with filters (FR-5.2).
        
        Returns:
            Tuple of (success, message, audit_logs)
        """
        try:
            logs = AuditLogModel.get_all(
                user_id=user_id,
                action=action,
                table_name=table_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            return True, f"Retrieved {len(logs)} audit log entries", logs
        except Exception as e:
            return False, f"Error retrieving audit logs: {str(e)}", None
    
    @staticmethod
    def get_record_history(table_name: str, record_id: int) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get audit history for a specific record (FR-5.2).
        
        Returns:
            Tuple of (success, message, history)
        """
        try:
            history = AuditLogModel.get_by_record(table_name, record_id)
            return True, f"Retrieved {len(history)} history entries", history
        except Exception as e:
            return False, f"Error retrieving record history: {str(e)}", None
    
    @staticmethod
    def get_user_activity(user_id: int, days_back: int = 30) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get recent activity for a user.
        
        Returns:
            Tuple of (success, message, activity)
        """
        try:
            activity = AuditLogModel.get_user_activity(user_id, days_back)
            return True, f"Retrieved {len(activity)} activity entries", activity
        except Exception as e:
            return False, f"Error retrieving user activity: {str(e)}", None
    
    @staticmethod
    def get_audit_statistics(days_back: int = 30) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get audit log statistics.
        
        Returns:
            Tuple of (success, message, statistics)
        """
        try:
            stats = AuditLogModel.get_statistics(days_back)
            return True, "Statistics retrieved successfully", stats
        except Exception as e:
            return False, f"Error retrieving statistics: {str(e)}", None
    
    @staticmethod
    def search_audit_logs(keyword: str) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Search audit logs by keyword.
        
        Returns:
            Tuple of (success, message, results)
        """
        if not keyword or len(keyword.strip()) < 2:
            return False, "Search keyword must be at least 2 characters", None
        
        try:
            results = AuditLogModel.search(keyword.strip())
            return True, f"Found {len(results)} matching entries", results
        except Exception as e:
            return False, f"Search failed: {str(e)}", None
    
    # ==========================================
    # SYSTEM SETTINGS
    # ==========================================
    
    @staticmethod
    def get_setting(key: str) -> Any:
        """Get a system setting value."""
        return SystemSettingsModel.get(key)
    
    @staticmethod
    def get_all_settings() -> Dict[str, Any]:
        """Get all system settings."""
        return SystemSettingsModel.get_all()
    
    @staticmethod
    def update_setting(key: str, value: Any, updated_by: int = None) -> Tuple[bool, str]:
        """
        Update a system setting.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            SystemSettingsModel.set(key, value, updated_by)
            return True, f"Setting '{key}' updated successfully"
        except Exception as e:
            return False, f"Error updating setting: {str(e)}"
    
    @staticmethod
    def update_barangay_info(
        barangay_name: str = None,
        municipality: str = None,
        province: str = None,
        captain_name: str = None,
        captain_title: str = None,
        updated_by: int = None
    ) -> Tuple[bool, str]:
        """
        Update barangay information settings.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if barangay_name:
                SystemSettingsModel.set('barangay_name', barangay_name, updated_by)
            if municipality:
                SystemSettingsModel.set('municipality', municipality, updated_by)
            if province:
                SystemSettingsModel.set('province', province, updated_by)
            if captain_name:
                SystemSettingsModel.set('captain_name', captain_name, updated_by)
            if captain_title:
                SystemSettingsModel.set('captain_title', captain_title, updated_by)
            
            return True, "Barangay information updated successfully"
        except Exception as e:
            return False, f"Error updating barangay info: {str(e)}"
    
    # ==========================================
    # SYSTEM DASHBOARD
    # ==========================================
    
    @staticmethod
    def get_system_dashboard() -> Dict[str, Any]:
        """Get comprehensive system administration dashboard data."""
        from models.resident import ResidentModel
        from models.blotter import BlotterCaseModel
        from database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Database stats
        cursor.execute("SELECT COUNT(*) FROM resident WHERE status = 'Active'")
        active_residents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM blotter_case")
        total_cases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM blotter_case WHERE status = 'Pending'")
        pending_cases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doc_log")
        total_documents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user WHERE is_active = 1")
        active_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_log")
        total_audit_entries = cursor.fetchone()[0]
        
        # Database file size
        from database import DATABASE_PATH
        db_size_bytes = os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
        db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
        
        conn.close()
        
        # Recent activity
        recent_logs = AuditLogModel.get_all(limit=10)
        
        # Backup info
        backups = BackupModel.get_backup_history()
        
        return {
            'database_stats': {
                'active_residents': active_residents,
                'total_cases': total_cases,
                'pending_cases': pending_cases,
                'total_documents': total_documents,
                'active_users': active_users,
                'total_audit_entries': total_audit_entries,
                'database_size_mb': db_size_mb
            },
            'recent_activity': recent_logs,
            'backup_count': len(backups),
            'latest_backup': backups[0] if backups else None,
            'settings': SystemSettingsModel.get_all(),
            'generated_at': datetime.now().isoformat()
        }
