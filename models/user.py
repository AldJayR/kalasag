"""
KALASAG - User Model
Authentication and user management operations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, hash_password, log_audit
from datetime import datetime
from typing import Optional, Dict, Any, List


class UserModel:
    """Model for User authentication and management."""
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: User's username
            password: User's password (plain text, will be hashed)
            
        Returns:
            User dict if authenticated, None otherwise
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute("""
            SELECT user_id, username, full_name, role, is_active
            FROM user
            WHERE username = ? AND password_hash = ? AND is_active = 1
        """, (username, password_hash))
        
        row = cursor.fetchone()
        
        if row:
            # Update last login timestamp
            cursor.execute("""
                UPDATE user SET last_login = ? WHERE user_id = ?
            """, (datetime.now().isoformat(), row['user_id']))
            conn.commit()
            
            user = dict(row)
            conn.close()
            return user
        
        conn.close()
        return None
    
    @staticmethod
    def create(username: str, password: str, full_name: str, role: str,
               created_by: int = None) -> int:
        """
        Create a new user.
        
        Args:
            username: Unique username
            password: Password (will be hashed)
            full_name: User's full name
            role: 'Captain', 'Secretary', 'Tanod', or 'Admin'
            created_by: ID of user creating this account
            
        Returns:
            New user ID
        """
        if role not in ('Captain', 'Secretary', 'Tanod', 'Admin'):
            raise ValueError(f"Invalid role: {role}")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        try:
            cursor.execute("""
                INSERT INTO user (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, full_name, role))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Log audit trail
            if created_by:
                log_audit(created_by, "CREATE_USER", "user", user_id, None,
                         f"Created user: {username} ({role})")
            
            conn.close()
            return user_id
            
        except Exception as e:
            conn.close()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Username '{username}' already exists")
            raise
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by ID (excluding password)."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, full_name, role, is_active, created_at, last_login
            FROM user
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    @staticmethod
    def get_all(include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all users."""
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT user_id, username, full_name, role, is_active, created_at, last_login
            FROM user
        """
        
        if not include_inactive:
            query += " WHERE is_active = 1"
        
        query += " ORDER BY full_name"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def update_password(user_id: int, new_password: str, 
                        updated_by: int = None) -> bool:
        """Update a user's password."""
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(new_password)
        
        cursor.execute("""
            UPDATE user SET password_hash = ? WHERE user_id = ?
        """, (password_hash, user_id))
        
        affected = cursor.rowcount
        conn.commit()
        
        if updated_by and affected > 0:
            log_audit(updated_by, "UPDATE_PASSWORD", "user", user_id, None, None)
        
        conn.close()
        return affected > 0
    
    @staticmethod
    def update(user_id: int, full_name: str = None, role: str = None,
               is_active: bool = None, updated_by: int = None) -> bool:
        """Update user information."""
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name)
        if role is not None:
            if role not in ('Captain', 'Secretary', 'Tanod', 'Admin'):
                conn.close()
                raise ValueError(f"Invalid role: {role}")
            updates.append("role = ?")
            params.append(role)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        
        if not updates:
            conn.close()
            return False
        
        params.append(user_id)
        query = f"UPDATE user SET {', '.join(updates)} WHERE user_id = ?"
        
        cursor.execute(query, params)
        affected = cursor.rowcount
        conn.commit()
        
        if updated_by and affected > 0:
            log_audit(updated_by, "UPDATE_USER", "user", user_id, None, str(updates))
        
        conn.close()
        return affected > 0
    
    @staticmethod
    def deactivate(user_id: int, deactivated_by: int = None) -> bool:
        """Deactivate a user (soft delete)."""
        return UserModel.update(user_id, is_active=False, updated_by=deactivated_by)
    
    @staticmethod
    def verify_password(user_id: int, password: str) -> bool:
        """Verify a user's current password."""
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute("""
            SELECT 1 FROM user WHERE user_id = ? AND password_hash = ?
        """, (user_id, password_hash))
        
        result = cursor.fetchone() is not None
        conn.close()
        
        return result
