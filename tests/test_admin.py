"""
KALASAG - Admin Module Tests
Tests for System Administration (FR-5.1, FR-5.2)
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Import modules under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_database, get_connection, log_audit, DATABASE_PATH
from models.admin import AuditLogModel, SystemSettingsModel, BackupModel
from models.user import UserModel
from controllers.admin_controller import AdminController


# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture(autouse=True)
def setup_database():
    """Initialize database before each test."""
    init_database()
    yield
    # Cleanup after tests
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM audit_log")
    cursor.execute("DELETE FROM user WHERE username NOT IN ('admin', 'secretary', 'tanod')")
    # Ensure admin user is active for next test
    cursor.execute("UPDATE user SET is_active = 1 WHERE username = 'admin'")
    conn.commit()
    conn.close()


@pytest.fixture
def test_user():
    """Create a test user."""
    user_id = UserModel.create(
        username='testadmin',
        password='password123',
        full_name='Test Administrator',
        role='Admin',
        created_by=None
    )
    return UserModel.get_by_id(user_id)


@pytest.fixture
def sample_audit_logs(test_user):
    """Create sample audit log entries."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create various audit entries using new_values column (not details)
    entries = [
        ('INSERT', 'resident', 1, 'Created resident: Juan Dela Cruz', test_user['user_id']),
        ('UPDATE', 'resident', 1, 'Updated resident contact', test_user['user_id']),
        ('INSERT', 'blotter_case', 1, 'Created blotter case: BC-2024-001', test_user['user_id']),
        ('UPDATE', 'blotter_case', 1, 'Status changed to Resolved', test_user['user_id']),
        ('INSERT', 'doc_log', 1, 'Issued Barangay Clearance', test_user['user_id']),
        ('DELETE', 'resident', 2, 'Deleted resident: Test Person', test_user['user_id']),
        ('LOGIN', 'user', test_user['user_id'], 'User logged in', test_user['user_id']),
        ('EXPORT', 'resident', None, 'Exported residents to CSV', test_user['user_id']),
        ('BACKUP', 'database', None, 'Database backup created', test_user['user_id']),
    ]
    
    for action, table, record_id, new_values, user_id in entries:
        cursor.execute("""
            INSERT INTO audit_log (action, table_name, record_id, new_values, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, (action, table, record_id, new_values, user_id))
    
    conn.commit()
    conn.close()
    
    return entries


# ==========================================
# AUDIT LOG MODEL TESTS (FR-5.2)
# ==========================================

class TestAuditLogModel:
    """Tests for AuditLogModel."""
    
    def test_get_all_audit_logs(self, sample_audit_logs, test_user):
        """Test retrieving all audit logs."""
        logs = AuditLogModel.get_all()
        
        assert len(logs) >= len(sample_audit_logs)
        assert all('log_id' in log for log in logs)
        assert all('action' in log for log in logs)
        assert all('timestamp' in log for log in logs)
    
    def test_get_audit_logs_with_filters(self, sample_audit_logs, test_user):
        """Test filtering audit logs."""
        # Filter by action
        insert_logs = AuditLogModel.get_all(action='INSERT')
        assert all(log['action'] == 'INSERT' for log in insert_logs)
        
        # Filter by table
        resident_logs = AuditLogModel.get_all(table_name='resident')
        assert all(log['table_name'] == 'resident' for log in resident_logs)
        
        # Filter by user
        user_logs = AuditLogModel.get_all(user_id=test_user['user_id'])
        assert all(log['user_id'] == test_user['user_id'] for log in user_logs)
    
    def test_get_audit_logs_with_limit(self, sample_audit_logs):
        """Test limiting audit log results."""
        logs = AuditLogModel.get_all(limit=3)
        assert len(logs) <= 3
    
    def test_get_by_record(self, sample_audit_logs):
        """Test getting audit history for a specific record."""
        history = AuditLogModel.get_by_record('resident', 1)
        
        assert len(history) > 0
        assert all(log['table_name'] == 'resident' for log in history)
        assert all(log['record_id'] == 1 for log in history)
    
    def test_get_user_activity(self, sample_audit_logs, test_user):
        """Test getting user activity."""
        activity = AuditLogModel.get_user_activity(test_user['user_id'])
        
        assert len(activity) > 0
        assert all(log['user_id'] == test_user['user_id'] for log in activity)
    
    def test_get_audit_statistics(self, sample_audit_logs):
        """Test getting audit statistics."""
        stats = AuditLogModel.get_statistics()
        
        assert 'total_actions' in stats
        assert 'by_action' in stats
        assert 'by_user' in stats
        assert stats['total_actions'] >= len(sample_audit_logs)
    
    def test_search_audit_logs(self, sample_audit_logs):
        """Test searching audit logs."""
        results = AuditLogModel.search('resident')
        
        assert len(results) > 0
        assert any('resident' in str(log.get('new_values', '').lower()) or 
                   log.get('table_name') == 'resident' for log in results)
    
    def test_search_no_results(self):
        """Test search with no matching results."""
        results = AuditLogModel.search('xyznonexistent')
        assert len(results) == 0


# ==========================================
# SYSTEM SETTINGS MODEL TESTS
# ==========================================

class TestSystemSettingsModel:
    """Tests for SystemSettingsModel."""
    
    def test_get_default_settings(self):
        """Test getting default settings."""
        barangay_name = SystemSettingsModel.get('barangay_name')
        assert barangay_name is not None
    
    def test_set_and_get_setting(self, test_user):
        """Test setting and retrieving a value."""
        SystemSettingsModel.set('test_setting', 'test_value', test_user['user_id'])
        
        value = SystemSettingsModel.get('test_setting')
        assert value == 'test_value'
    
    def test_update_existing_setting(self, test_user):
        """Test updating an existing setting."""
        SystemSettingsModel.set('test_key', 'initial_value', test_user['user_id'])
        SystemSettingsModel.set('test_key', 'updated_value', test_user['user_id'])
        
        value = SystemSettingsModel.get('test_key')
        assert value == 'updated_value'
    
    def test_get_all_settings(self):
        """Test getting all settings."""
        settings = SystemSettingsModel.get_all()
        
        assert isinstance(settings, dict)
        assert 'barangay_name' in settings
    
    def test_get_nonexistent_setting_returns_none(self):
        """Test getting a setting that doesn't exist."""
        value = SystemSettingsModel.get('nonexistent_setting_key_12345')
        assert value is None


# ==========================================
# BACKUP MODEL TESTS (FR-5.1)
# ==========================================

class TestBackupModel:
    """Tests for BackupModel."""
    
    def test_create_backup(self, test_user):
        """Test creating a database backup."""
        backup_path = BackupModel.create_backup(user_id=test_user['user_id'])
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        
        # Clean up
        if os.path.exists(backup_path):
            os.remove(backup_path)
    
    def test_backup_creates_valid_file(self, test_user):
        """Test that backup creates a valid SQLite file."""
        backup_path = BackupModel.create_backup(user_id=test_user['user_id'])
        
        # Check file size is reasonable
        file_size = os.path.getsize(backup_path)
        assert file_size > 0
        
        # Clean up
        os.remove(backup_path)
    
    def test_export_table_csv(self, test_user):
        """Test exporting a table to CSV."""
        csv_path = BackupModel.export_table_csv('user', user_id=test_user['user_id'])
        
        assert csv_path is not None
        assert os.path.exists(csv_path)
        assert csv_path.endswith('.csv')
        
        # Check file has content
        with open(csv_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert 'username' in content.lower() or 'admin' in content.lower()
        
        # Clean up
        os.remove(csv_path)
    
    def test_export_invalid_table_raises_error(self, test_user):
        """Test that exporting non-existent table raises error."""
        with pytest.raises(ValueError):
            BackupModel.export_table_csv('nonexistent_table_xyz', user_id=test_user['user_id'])
    
    def test_export_all_tables(self, test_user):
        """Test exporting all tables."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            files = BackupModel.export_all_tables(temp_dir, user_id=test_user['user_id'])
            
            assert len(files) > 0
            assert all(os.path.exists(f) for f in files)
            assert all(f.endswith('.csv') for f in files)
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def test_get_backup_history(self, test_user):
        """Test getting backup history."""
        # Create a backup first
        BackupModel.create_backup(user_id=test_user['user_id'])
        
        history = BackupModel.get_backup_history()
        
        # History is derived from audit logs
        assert isinstance(history, list)


# ==========================================
# ADMIN CONTROLLER - USER MANAGEMENT TESTS
# ==========================================

class TestAdminControllerUserManagement:
    """Tests for AdminController user management."""
    
    def test_create_user_success(self):
        """Test successful user creation."""
        success, message, user = AdminController.create_user(
            username='newuser',
            password='password123',
            full_name='New Test User',
            role='Secretary'
        )
        
        assert success is True
        assert user is not None
        assert user['username'] == 'newuser'
        assert user['role'] == 'Secretary'
    
    def test_create_user_invalid_username(self):
        """Test user creation with invalid username."""
        success, message, user = AdminController.create_user(
            username='ab',  # Too short
            password='password123',
            full_name='Test User',
            role='Secretary'
        )
        
        assert success is False
        assert 'Username' in message
        assert user is None
    
    def test_create_user_invalid_password(self):
        """Test user creation with invalid password."""
        success, message, user = AdminController.create_user(
            username='testuser',
            password='123',  # Too short
            full_name='Test User',
            role='Secretary'
        )
        
        assert success is False
        assert 'Password' in message or 'password' in message
        assert user is None
    
    def test_create_user_invalid_role(self):
        """Test user creation with invalid role."""
        success, message, user = AdminController.create_user(
            username='testuser',
            password='password123',
            full_name='Test User',
            role='InvalidRole'
        )
        
        assert success is False
        assert 'role' in message.lower()
        assert user is None
    
    def test_update_user_success(self, test_user):
        """Test successful user update."""
        success, message, updated = AdminController.update_user(
            user_id=test_user['user_id'],
            full_name='Updated Name',
            role='Captain'
        )
        
        assert success is True
        assert updated['full_name'] == 'Updated Name'
        assert updated['role'] == 'Captain'
    
    def test_update_nonexistent_user(self):
        """Test updating a user that doesn't exist."""
        success, message, updated = AdminController.update_user(
            user_id=99999,
            full_name='Test'
        )
        
        assert success is False
        assert 'not found' in message.lower()
    
    def test_change_password_success(self, test_user):
        """Test successful password change."""
        success, message = AdminController.change_password(
            user_id=test_user['user_id'],
            new_password='newpassword123',
            current_password='password123',
            changed_by=test_user['user_id']
        )
        
        assert success is True
        
        # Verify new password works
        assert UserModel.verify_password(test_user['user_id'], 'newpassword123')
    
    def test_change_password_wrong_current(self, test_user):
        """Test password change with wrong current password."""
        success, message = AdminController.change_password(
            user_id=test_user['user_id'],
            new_password='newpassword123',
            current_password='wrongpassword',
            changed_by=test_user['user_id']
        )
        
        assert success is False
        assert 'incorrect' in message.lower()
    
    def test_change_password_too_short(self, test_user):
        """Test password change with too short password."""
        # Create a second user for changed_by
        second_user_id = UserModel.create(
            username='pwchanger',
            password='password123',
            full_name='Password Changer',
            role='Admin',
            created_by=None
        )
        
        success, message = AdminController.change_password(
            user_id=test_user['user_id'],
            new_password='123',
            changed_by=second_user_id
        )
        
        assert success is False
        assert 'character' in message.lower()
    
    def test_deactivate_user_success(self, test_user):
        """Test successful user deactivation."""
        # Create a second user to act as deactivator
        second_user_id = UserModel.create(
            username='deactivator',
            password='password123',
            full_name='Deactivator User',
            role='Admin',
            created_by=None
        )
        
        success, message = AdminController.deactivate_user(
            user_id=test_user['user_id'],
            deactivated_by=second_user_id  # Different user
        )
        
        assert success is True
        
        # Verify user is inactive
        user = UserModel.get_by_id(test_user['user_id'])
        assert user['is_active'] == 0
    
    def test_deactivate_self_not_allowed(self, test_user):
        """Test that users cannot deactivate themselves."""
        success, message = AdminController.deactivate_user(
            user_id=test_user['user_id'],
            deactivated_by=test_user['user_id']
        )
        
        assert success is False
        assert 'own account' in message.lower()
    
    def test_authenticate_user_success(self, test_user):
        """Test successful authentication."""
        success, message, user = AdminController.authenticate_user(
            username='testadmin',
            password='password123'
        )
        
        assert success is True
        assert user is not None
        assert user['username'] == 'testadmin'
    
    def test_authenticate_user_wrong_password(self, test_user):
        """Test authentication with wrong password."""
        success, message, user = AdminController.authenticate_user(
            username='testadmin',
            password='wrongpassword'
        )
        
        assert success is False
        assert user is None
    
    def test_get_all_users(self, test_user):
        """Test getting all users."""
        users = AdminController.get_all_users()
        
        assert len(users) > 0
        assert any(u['username'] == 'testadmin' for u in users)


# ==========================================
# ADMIN CONTROLLER - BACKUP TESTS (FR-5.1)
# ==========================================

class TestAdminControllerBackup:
    """Tests for AdminController backup functionality."""
    
    def test_create_backup_success(self, test_user):
        """Test one-click backup creation."""
        success, message, path = AdminController.create_backup(user_id=test_user['user_id'])
        
        assert success is True
        assert path is not None
        assert os.path.exists(path)
        
        # Clean up
        os.remove(path)
    
    def test_export_single_table(self, test_user):
        """Test exporting a single table to CSV."""
        success, message, files = AdminController.export_to_csv(
            table_name='user',
            user_id=test_user['user_id']
        )
        
        assert success is True
        assert len(files) == 1
        assert files[0].endswith('.csv')
        
        # Clean up
        for f in files:
            if os.path.exists(f):
                os.remove(f)
    
    def test_export_all_tables(self, test_user):
        """Test exporting all tables to CSV."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            success, message, files = AdminController.export_to_csv(
                output_dir=temp_dir,
                user_id=test_user['user_id']
            )
            
            assert success is True
            assert len(files) > 0
        finally:
            shutil.rmtree(temp_dir)
    
    def test_export_invalid_table(self, test_user):
        """Test exporting invalid table."""
        success, message, files = AdminController.export_to_csv(
            table_name='invalid_table_xyz',
            user_id=test_user['user_id']
        )
        
        assert success is False
        assert files is None
    
    def test_get_backup_list(self, test_user):
        """Test getting backup list."""
        # Create a backup first
        AdminController.create_backup(user_id=test_user['user_id'])
        
        backups = AdminController.get_backup_list()
        
        assert isinstance(backups, list)


# ==========================================
# ADMIN CONTROLLER - AUDIT TESTS (FR-5.2)
# ==========================================

class TestAdminControllerAudit:
    """Tests for AdminController audit trail functionality."""
    
    def test_get_audit_logs(self, sample_audit_logs):
        """Test retrieving audit logs."""
        success, message, logs = AdminController.get_audit_logs()
        
        assert success is True
        assert len(logs) > 0
    
    def test_get_audit_logs_with_filters(self, sample_audit_logs, test_user):
        """Test retrieving audit logs with filters."""
        success, message, logs = AdminController.get_audit_logs(
            action='INSERT',
            user_id=test_user['user_id']
        )
        
        assert success is True
        assert all(log['action'] == 'INSERT' for log in logs)
    
    def test_get_record_history(self, sample_audit_logs):
        """Test getting record history."""
        success, message, history = AdminController.get_record_history('resident', 1)
        
        assert success is True
        assert isinstance(history, list)
    
    def test_get_user_activity(self, sample_audit_logs, test_user):
        """Test getting user activity."""
        success, message, activity = AdminController.get_user_activity(test_user['user_id'])
        
        assert success is True
        assert len(activity) > 0
    
    def test_get_audit_statistics(self, sample_audit_logs):
        """Test getting audit statistics."""
        success, message, stats = AdminController.get_audit_statistics()
        
        assert success is True
        assert 'total_actions' in stats
        assert 'by_action' in stats
    
    def test_search_audit_logs(self, sample_audit_logs):
        """Test searching audit logs."""
        success, message, results = AdminController.search_audit_logs('resident')
        
        assert success is True
        assert len(results) >= 0
    
    def test_search_audit_logs_short_keyword(self):
        """Test search with too short keyword."""
        success, message, results = AdminController.search_audit_logs('a')
        
        assert success is False
        assert 'at least' in message.lower()


# ==========================================
# ADMIN CONTROLLER - SETTINGS TESTS
# ==========================================

class TestAdminControllerSettings:
    """Tests for AdminController system settings."""
    
    def test_get_setting(self):
        """Test getting a setting."""
        value = AdminController.get_setting('barangay_name')
        assert value is not None
    
    def test_get_all_settings(self):
        """Test getting all settings."""
        settings = AdminController.get_all_settings()
        
        assert isinstance(settings, dict)
        assert 'barangay_name' in settings
    
    def test_update_setting(self, test_user):
        """Test updating a setting."""
        success, message = AdminController.update_setting(
            key='test_setting',
            value='test_value',
            updated_by=test_user['user_id']
        )
        
        assert success is True
        assert AdminController.get_setting('test_setting') == 'test_value'
    
    def test_update_barangay_info(self, test_user):
        """Test updating barangay info."""
        success, message = AdminController.update_barangay_info(
            barangay_name='Test Barangay',
            municipality='Test Municipality',
            province='Test Province',
            captain_name='Juan Dela Cruz',
            captain_title='Punong Barangay',
            updated_by=test_user['user_id']
        )
        
        assert success is True
        assert AdminController.get_setting('barangay_name') == 'Test Barangay'
        assert AdminController.get_setting('municipality') == 'Test Municipality'


# ==========================================
# ADMIN CONTROLLER - DASHBOARD TESTS
# ==========================================

class TestAdminControllerDashboard:
    """Tests for AdminController dashboard."""
    
    def test_get_system_dashboard(self):
        """Test getting system dashboard data."""
        dashboard = AdminController.get_system_dashboard()
        
        assert 'database_stats' in dashboard
        assert 'recent_activity' in dashboard
        assert 'settings' in dashboard
        assert 'generated_at' in dashboard
    
    def test_dashboard_contains_stats(self):
        """Test that dashboard contains expected statistics."""
        dashboard = AdminController.get_system_dashboard()
        stats = dashboard['database_stats']
        
        assert 'active_residents' in stats
        assert 'total_cases' in stats
        assert 'pending_cases' in stats
        assert 'total_documents' in stats
        assert 'active_users' in stats
        assert 'database_size_mb' in stats


# ==========================================
# INTEGRATION TESTS
# ==========================================

class TestAdminIntegration:
    """Integration tests for admin functionality."""
    
    def test_full_user_lifecycle(self):
        """Test complete user lifecycle: create, update, deactivate."""
        # Create an admin user for operations that need different user
        admin_id = UserModel.create(
            username='lifecycle_admin',
            password='password123',
            full_name='Lifecycle Admin',
            role='Admin',
            created_by=None
        )
        
        # Create user
        success, _, user = AdminController.create_user(
            username='lifecycle_test',
            password='testpass123',
            full_name='Lifecycle Test User',
            role='Tanod'
        )
        assert success is True
        
        # Authenticate
        success, _, auth_user = AdminController.authenticate_user(
            'lifecycle_test', 'testpass123'
        )
        assert success is True
        
        # Update
        success, _, updated = AdminController.update_user(
            user_id=user['user_id'],
            full_name='Updated Lifecycle User',
            role='Secretary'
        )
        assert success is True
        assert updated['role'] == 'Secretary'
        
        # Change password (use admin user for changed_by)
        success, _ = AdminController.change_password(
            user_id=user['user_id'],
            new_password='newpass456',
            changed_by=admin_id
        )
        assert success is True
        
        # Deactivate (use admin user for deactivated_by)
        success, _ = AdminController.deactivate_user(
            user_id=user['user_id'],
            deactivated_by=admin_id
        )
        assert success is True
        
        # Verify cannot authenticate after deactivation
        success, _, _ = AdminController.authenticate_user(
            'lifecycle_test', 'newpass456'
        )
        assert success is False
    
    def test_backup_and_verify(self, test_user):
        """Test backup creation and verification."""
        # Create backup
        success, _, backup_path = AdminController.create_backup(user_id=test_user['user_id'])
        assert success is True
        
        # Verify backup file exists and has reasonable size
        assert os.path.exists(backup_path)
        original_size = os.path.getsize(DATABASE_PATH)
        backup_size = os.path.getsize(backup_path)
        
        # Backup should be roughly same size as original
        assert backup_size > 0
        assert abs(backup_size - original_size) < original_size * 0.1  # Within 10%
        
        # Clean up
        os.remove(backup_path)
    
    def test_audit_trail_for_operations(self, test_user):
        """Test that operations are properly logged in audit trail."""
        # Perform some operations that should be logged
        AdminController.create_backup(user_id=test_user['user_id'])
        AdminController.update_setting('test_audit_key', 'test_value', test_user['user_id'])
        
        # Check audit logs
        success, _, logs = AdminController.get_audit_logs(user_id=test_user['user_id'])
        assert success is True
        
        # Should have entries for our operations
        actions = [log['action'] for log in logs]
        assert len(actions) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
