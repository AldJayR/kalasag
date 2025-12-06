"""
KALASAG - Analytics Model
Data access layer for analytics and BI queries.
Implements FR-4.1, FR-4.2, FR-4.3
"""

import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from database import get_connection


class AnalyticsModel:
    """Model for analytics data queries."""
    
    @staticmethod
    def _calculate_severity_level(count: int) -> str:
        """Calculate severity level based on incident count."""
        if count == 0:
            return 'safe'
        elif count <= 3:
            return 'caution'
        else:
            return 'hotspot'

    @staticmethod
    def _get_severity_color(level: str) -> str:
        """Get color code for severity level."""
        colors = {
            'safe': '#28a745',      # Green
            'caution': '#ffc107',   # Yellow
            'hotspot': '#dc3545'    # Red
        }
        return colors.get(level, '#6c757d')

    @staticmethod
    def _format_hour(hour: int) -> str:
        """Format hour (0-23) to 12-hour format with AM/PM."""
        if hour == 0:
            return "12:00 AM"
        elif hour == 12:
            return "12:00 PM"
        elif hour < 12:
            return f"{hour}:00 AM"
        else:
            return f"{hour-12}:00 PM"

    @staticmethod
    def _get_time_period(hour: int) -> str:
        """Get time period classification."""
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 18:
            return "Afternoon"
        elif 18 <= hour < 22:
            return "Evening"
        else:
            return "Night"

    @staticmethod
    def get_incident_count_by_purok(days_back: int = 30) -> List[Dict]:
        """
        Get incident counts grouped by purok for heatmap visualization.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of dicts with purok_id, name, count, and risk_level
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT 
                    p.purok_id,
                    p.purok_name,
                    COUNT(bc.case_id) as incident_count
                FROM purok p
                LEFT JOIN blotter_case bc ON p.purok_id = bc.purok_id AND bc.date_time >= ?
                GROUP BY p.purok_id, p.purok_name
                ORDER BY incident_count DESC
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
            
            # Calculate risk levels based on count
            results = []
            for row in rows:
                count = row[2] or 0
                
                # Determine risk level
                risk_level = AnalyticsModel._calculate_severity_level(count)
                color = AnalyticsModel._get_severity_color(risk_level)
                
                results.append({
                    'purok_id': row[0],
                    'purok_name': row[1],
                    'name': row[1],
                    'count': count,
                    'incident_count': count,
                    'risk_level': risk_level,
                    'severity_level': risk_level,
                    'severity_color': color
                })
            
            return results
            
        finally:
            conn.close()
    
    @staticmethod
    def get_incidents_by_type(days_back: int = 30) -> List[Dict]:
        """Alias for get_incident_count_by_type."""
        return AnalyticsModel.get_incident_count_by_type(days_back)

    @staticmethod
    def get_incident_count_by_type(days_back: int = 30) -> List[Dict]:
        """
        Get incident counts grouped by incident type.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of dicts with type_id, name, count
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT 
                    it.type_id,
                    it.name,
                    COUNT(bc.case_id) as incident_count
                FROM incident_type it
                LEFT JOIN blotter_case bc ON it.type_id = bc.type_id AND bc.date_time >= ?
                GROUP BY it.type_id, it.name
                ORDER BY incident_count DESC
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
            
            return [
                {
                    'type_id': row[0],
                    'name': row[1],
                    'type_name': row[1],
                    'count': row[2] or 0,
                    'incident_count': row[2] or 0
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    @staticmethod
    def get_incidents_by_time_of_day(days_back: int = 30) -> List[Dict]:
        """Get incidents grouped by hour of day."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT 
                    strftime('%H', date_time) as hour,
                    COUNT(*) as count
                FROM blotter_case
                WHERE date_time >= ?
                GROUP BY hour
                ORDER BY hour
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
            counts = {int(row[0]): row[1] for row in rows}
            
            results = []
            for hour in range(24):
                count = counts.get(hour, 0)
                results.append({
                    'hour': hour,
                    'incident_count': count,
                    'time_label': AnalyticsModel._format_hour(hour),
                    'period': AnalyticsModel._get_time_period(hour)
                })
            
            return results
            
        finally:
            conn.close()

    @staticmethod
    def get_incidents_by_day_of_week(days_back: int = 30) -> List[Dict]:
        """Get incidents grouped by day of week."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            # SQLite strftime %w returns 0-6 (Sunday-Saturday)
            cursor.execute("""
                SELECT 
                    strftime('%w', date_time) as day_idx,
                    COUNT(*) as count
                FROM blotter_case
                WHERE date_time >= ?
                GROUP BY day_idx
                ORDER BY day_idx
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
            counts = {int(row[0]): row[1] for row in rows}
            
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            results = []
            
            for i, day_name in enumerate(days):
                results.append({
                    'day_index': i,
                    'day_name': day_name,
                    'incident_count': counts.get(i, 0)
                })
            
            return results
            
        finally:
            conn.close()

    @staticmethod
    def get_most_dangerous_hours(days_back: int = 30, top_n: int = 3) -> List[Dict]:
        """Get the hours with most incidents."""
        data = AnalyticsModel.get_incidents_by_time_of_day(days_back)
        sorted_data = sorted(data, key=lambda x: x['incident_count'], reverse=True)
        return sorted_data[:top_n]

    @staticmethod
    def get_incident_count_by_location(days_back: int = 30) -> List[Dict]:
        """
        Get incident counts grouped by location.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of dicts with location, count
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT 
                    p.purok_name as location,
                    COUNT(*) as incident_count
                FROM blotter_case bc
                LEFT JOIN purok p ON bc.purok_id = p.purok_id
                WHERE bc.date_time >= ?
                GROUP BY bc.purok_id
                ORDER BY incident_count DESC
                LIMIT 20
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
            
            return [
                {
                    'location': row[0] or 'Unknown',
                    'count': row[1]
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    @staticmethod
    def get_monthly_trend(months_back: int = 6) -> List[Dict]:
        """
        Get monthly incident trend.
        
        Args:
            months_back: Number of months to look back
            
        Returns:
            List of dicts with month, year, count
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', date_time) as month_str,
                    strftime('%Y', date_time) as year,
                    strftime('%m', date_time) as month_num,
                    COUNT(*) as incident_count
                FROM blotter_case
                WHERE date_time >= date('now', ? || ' months')
                GROUP BY month_str
                ORDER BY month_str
            """, (f'-{months_back}',))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # Get month name from month number
                try:
                    month_num = int(row[2])
                    month_name = datetime(2000, month_num, 1).strftime('%B')
                except (ValueError, IndexError):
                    month_name = row[0]
                
                results.append({
                    'month': row[0],
                    'year': row[1],
                    'month_name': month_name,
                    'count': row[3],
                    'incident_count': row[3]
                })
            
            return results
            
        finally:
            conn.close()

    @staticmethod
    def generate_patrol_recommendations(days_back: int = 30) -> List[Dict]:
        """Generate patrol recommendations based on hotspots and time analysis."""
        # Get hotspot puroks
        puroks = AnalyticsModel.get_incident_count_by_purok(days_back)
        hotspots = [p for p in puroks if p['severity_level'] in ('hotspot', 'caution')]
        
        recommendations = []
        priority = 1
        
        for purok in hotspots:
            # Analyze peak times for this purok
            conn = get_connection()
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT strftime('%H', date_time) as hour, COUNT(*) as count
                FROM blotter_case
                WHERE purok_id = ? AND date_time >= ?
                GROUP BY hour
                ORDER BY count DESC
                LIMIT 1
            """, (purok['purok_id'], cutoff_date))
            
            row = cursor.fetchone()
            conn.close()
            
            peak_hour = int(row[0]) if row else 0
            time_range = f"{AnalyticsModel._format_hour(peak_hour)} - {AnalyticsModel._format_hour((peak_hour + 4) % 24)}"
            
            recommendations.append({
                'priority': priority,
                'purok_name': purok['purok_name'],
                'time_range': time_range,
                'reason': f"High incident count ({purok['incident_count']}) mostly around {AnalyticsModel._format_hour(peak_hour)}",
                'severity_level': purok['severity_level']
            })
            priority += 1
            
        # If no hotspots, provide general recommendation
        if not recommendations:
            recommendations.append({
                'priority': 1,
                'purok_name': "All Areas",
                'time_range': "8:00 PM - 12:00 AM",
                'reason': "Routine patrol (No hotspots detected)",
                'severity_level': 'safe'
            })
            
        return recommendations

    @staticmethod
    def get_dashboard_summary(days_back: int = 30) -> Dict:
        """Get summary statistics for dashboard."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            # Total incidents
            cursor.execute("SELECT COUNT(*) FROM blotter_case WHERE date_time >= ?", (cutoff_date,))
            total_incidents = cursor.fetchone()[0]
            
            # Pending cases
            cursor.execute("SELECT COUNT(*) FROM blotter_case WHERE status = 'Pending'")
            pending_cases = cursor.fetchone()[0]
            
            # Total residents
            cursor.execute("SELECT COUNT(*) FROM resident WHERE status = 'Active'")
            total_residents = cursor.fetchone()[0]
            
            # Hotspot counts
            purok_data = AnalyticsModel.get_incident_count_by_purok(days_back)
            hotspot_count = sum(1 for p in purok_data if p['severity_level'] == 'hotspot')
            caution_count = sum(1 for p in purok_data if p['severity_level'] == 'caution')
            safe_count = sum(1 for p in purok_data if p['severity_level'] == 'safe')
            
            return {
                'total_incidents': total_incidents,
                'pending_cases': pending_cases,
                'total_residents': total_residents,
                'hotspot_count': hotspot_count,
                'caution_count': caution_count,
                'safe_count': safe_count,
                'start_date': cutoff_date,
                'end_date': datetime.now().strftime("%Y-%m-%d")
            }
            
        finally:
            conn.close()
    
    @staticmethod
    def get_demographic_by_gender() -> List[Dict]:
        """Get resident count by gender."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    sex as gender,
                    COUNT(*) as count
                FROM resident
                WHERE status = 'Active'
                GROUP BY sex
            """)
            
            rows = cursor.fetchall()
            
            return [
                {
                    'gender': row[0] or 'Unknown',
                    'count': row[1]
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    @staticmethod
    def get_demographic_by_civil_status() -> List[Dict]:
        """Get resident count by civil status."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    civil_status,
                    COUNT(*) as count
                FROM resident
                GROUP BY civil_status
            """)
            
            rows = cursor.fetchall()
            
            return [
                {
                    'civil_status': row[0] or 'Unknown',
                    'count': row[1]
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    @staticmethod
    def get_demographic_by_purok() -> List[Dict]:
        """Get resident count by purok."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    p.purok_id,
                    p.purok_name,
                    COUNT(r.res_id) as count
                FROM purok p
                LEFT JOIN resident r ON p.purok_id = r.purok_id AND r.status = 'Active'
                GROUP BY p.purok_id, p.purok_name
                ORDER BY count DESC
            """)
            
            rows = cursor.fetchall()
            
            return [
                {
                    'purok_id': row[0],
                    'purok_name': row[1],
                    'name': row[1],
                    'count': row[2] or 0
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    @staticmethod
    def get_demographic_by_age_group() -> List[Dict]:
        """Get resident count by age group."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    CASE
                        WHEN (julianday('now') - julianday(birthdate)) / 365.25 < 18 THEN 'Minor (0-17)'
                        WHEN (julianday('now') - julianday(birthdate)) / 365.25 < 30 THEN 'Young Adult (18-29)'
                        WHEN (julianday('now') - julianday(birthdate)) / 365.25 < 45 THEN 'Adult (30-44)'
                        WHEN (julianday('now') - julianday(birthdate)) / 365.25 < 60 THEN 'Middle Age (45-59)'
                        ELSE 'Senior (60+)'
                    END as age_group,
                    COUNT(*) as count
                FROM resident
                WHERE birthdate IS NOT NULL
                GROUP BY age_group
                ORDER BY 
                    CASE age_group
                        WHEN 'Minor (0-17)' THEN 1
                        WHEN 'Young Adult (18-29)' THEN 2
                        WHEN 'Adult (30-44)' THEN 3
                        WHEN 'Middle Age (45-59)' THEN 4
                        WHEN 'Senior (60+)' THEN 5
                    END
            """)
            
            rows = cursor.fetchall()
            
            return [
                {
                    'age_group': row[0],
                    'count': row[1]
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    @staticmethod
    def get_voter_statistics() -> Dict:
        """Get voter registration statistics (placeholder - voter_status not in schema)."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # voter_status column doesn't exist in current schema
            # Return count of active residents as placeholder
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM resident
                WHERE status = 'Active'
            """)
            
            row = cursor.fetchone()
            total = row[0] or 0
            
            return {
                'registered': 0,
                'not_registered': total,
                'total': total,
                'percentage': 0.0
            }
            
        finally:
            conn.close()

    @staticmethod
    def get_case_status_summary() -> List[Dict]:
        """Get case count by status."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM blotter_case
                GROUP BY status
            """)
            
            rows = cursor.fetchall()
            
            return [
                {
                    'status': row[0] or 'Unknown',
                    'count': row[1]
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    @staticmethod
    def get_document_statistics(days_back: int = 30) -> Dict:
        """Get document issuance statistics."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT 
                    document_type,
                    COUNT(*) as count,
                    SUM(amount) as total_amount
                FROM doc_log
                WHERE issue_date >= ?
                GROUP BY document_type
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
            
            by_type = [
                {
                    'document_type': row[0],
                    'count': row[1],
                    'total_amount': row[2] or 0
                }
                for row in rows
            ]
            
            # Get totals
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_count,
                    SUM(amount) as total_amount
                FROM doc_log
                WHERE issue_date >= ?
            """, (cutoff_date,))
            
            total_row = cursor.fetchone()
            
            return {
                'by_type': by_type,
                'total_count': total_row[0] or 0,
                'total_amount': total_row[1] or 0
            }
            
        finally:
            conn.close()
    
    @staticmethod
    def predict_risk_level(purok_id: int, days_back: int = 90) -> Dict:
        """
        Predict risk level for a purok based on historical data.
        Simple prediction based on incident trends.
        
        Args:
            purok_id: Purok to analyze
            days_back: Historical period to analyze
            
        Returns:
            Dict with prediction data
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get historical incidents for this purok
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT COUNT(bc.case_id) as incident_count
                FROM blotter_case bc
                JOIN case_involvement ci ON bc.case_id = ci.case_id
                JOIN resident r ON ci.resident_id = r.resident_id
                JOIN household h ON r.household_id = h.household_id
                WHERE h.purok_id = ? AND bc.date_time >= ?
            """, (purok_id, cutoff_date))
            
            row = cursor.fetchone()
            historical_count = row[0] or 0
            
            # Get recent incidents (last 30 days)
            recent_cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT COUNT(bc.case_id) as incident_count
                FROM blotter_case bc
                JOIN case_involvement ci ON bc.case_id = ci.case_id
                JOIN resident r ON ci.resident_id = r.resident_id
                JOIN household h ON r.household_id = h.household_id
                WHERE h.purok_id = ? AND bc.date_time >= ?
            """, (purok_id, recent_cutoff))
            
            row = cursor.fetchone()
            recent_count = row[0] or 0
            
            # Calculate trend
            avg_monthly = historical_count / (days_back / 30) if days_back > 0 else 0
            
            if recent_count > avg_monthly * 1.5:
                trend = 'increasing'
                risk_prediction = 'high'
            elif recent_count < avg_monthly * 0.5:
                trend = 'decreasing'
                risk_prediction = 'low'
            else:
                trend = 'stable'
                risk_prediction = 'medium' if recent_count > 0 else 'low'
            
            return {
                'purok_id': purok_id,
                'historical_count': historical_count,
                'recent_count': recent_count,
                'avg_monthly': round(avg_monthly, 2),
                'trend': trend,
                'risk_prediction': risk_prediction
            }
            
        finally:
            conn.close()
