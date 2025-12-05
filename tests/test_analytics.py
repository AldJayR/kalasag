"""
KALASAG - Test Suite for Analytics Module
TDD tests for Intelligence & Analytics.
Tests FR-4.1, FR-4.2, FR-4.3
"""

import pytest
import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from database import init_database, seed_default_data, get_connection
from models.analytics import AnalyticsModel
from models.resident import ResidentModel
from models.blotter import BlotterCaseModel, CaseInvolvementModel
from controllers.analytics_controller import AnalyticsController


# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="module")
def setup_database():
    """Set up test database with sample data."""
    database.DATABASE_PATH = "test_kalasag_analytics.db"
    
    # Remove existing test database
    if os.path.exists("test_kalasag_analytics.db"):
        os.remove("test_kalasag_analytics.db")
    
    init_database()
    seed_default_data()
    
    yield
    
    # Cleanup
    if os.path.exists("test_kalasag_analytics.db"):
        os.remove("test_kalasag_analytics.db")


@pytest.fixture
def sample_residents(setup_database):
    """Create sample residents in different puroks."""
    residents = []
    
    # Get purok IDs
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT purok_id FROM purok LIMIT 3")
    puroks = [row['purok_id'] for row in cursor.fetchall()]
    conn.close()
    
    for i, purok_id in enumerate(puroks):
        res_id = ResidentModel.create(
            first_name=f"Test{i}",
            last_name=f"Resident{i}",
            purok_id=purok_id,
            status="Active"
        )
        residents.append({'res_id': res_id, 'purok_id': purok_id})
    
    return residents


@pytest.fixture
def sample_incidents(setup_database, sample_residents):
    """Create sample incidents for analytics testing."""
    incidents = []
    
    # Get incident types
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT type_id FROM incident_type LIMIT 3")
    types = [row['type_id'] for row in cursor.fetchall()]
    conn.close()
    
    # Create incidents at various times
    now = datetime.now()
    
    # Purok 1: 5 incidents (Hotspot) - various hours
    for i in range(5):
        hour = 18 + (i % 4)  # Evening hours mostly
        incident_time = (now - timedelta(days=i, hours=now.hour-hour)).strftime("%Y-%m-%d %H:%M:%S")
        
        case_id, _ = BlotterCaseModel.create(
            date_time=incident_time,
            narrative=f"Test incident {i} in purok 1",
            purok_id=sample_residents[0]['purok_id'],
            type_id=types[i % len(types)]
        )
        incidents.append(case_id)
    
    # Purok 2: 2 incidents (Caution)
    for i in range(2):
        hour = 14 + i  # Afternoon
        incident_time = (now - timedelta(days=i+5, hours=now.hour-hour)).strftime("%Y-%m-%d %H:%M:%S")
        
        case_id, _ = BlotterCaseModel.create(
            date_time=incident_time,
            narrative=f"Test incident {i} in purok 2",
            purok_id=sample_residents[1]['purok_id'],
            type_id=types[0]
        )
        incidents.append(case_id)
    
    # Purok 3: 0 incidents (Safe) - no incidents created
    
    return incidents


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for chart output."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


# ============================================
# ANALYTICS MODEL TESTS - FR-4.1 Crime Heatmap
# ============================================

class TestCrimeHeatmap:
    """Test Crime Heatmap functionality (FR-4.1)."""
    
    def test_get_incident_count_by_purok(self, setup_database, sample_incidents):
        """FR-4.1: Test getting incident counts by purok."""
        data = AnalyticsModel.get_incident_count_by_purok(days_back=30)
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify structure
        first_item = data[0]
        assert 'purok_id' in first_item
        assert 'purok_name' in first_item
        assert 'incident_count' in first_item
        assert 'severity_level' in first_item
        assert 'severity_color' in first_item
    
    def test_severity_level_calculation_safe(self, setup_database):
        """FR-4.1: Test severity level for 0 incidents (Safe/Green)."""
        level = AnalyticsModel._calculate_severity_level(0)
        assert level == 'safe'
    
    def test_severity_level_calculation_caution(self, setup_database):
        """FR-4.1: Test severity level for 1-3 incidents (Caution/Yellow)."""
        assert AnalyticsModel._calculate_severity_level(1) == 'caution'
        assert AnalyticsModel._calculate_severity_level(2) == 'caution'
        assert AnalyticsModel._calculate_severity_level(3) == 'caution'
    
    def test_severity_level_calculation_hotspot(self, setup_database):
        """FR-4.1: Test severity level for >3 incidents (Hotspot/Red)."""
        assert AnalyticsModel._calculate_severity_level(4) == 'hotspot'
        assert AnalyticsModel._calculate_severity_level(10) == 'hotspot'
    
    def test_severity_colors(self, setup_database):
        """FR-4.1: Test severity color codes."""
        assert AnalyticsModel._get_severity_color('safe') == '#28a745'      # Green
        assert AnalyticsModel._get_severity_color('caution') == '#ffc107'   # Yellow
        assert AnalyticsModel._get_severity_color('hotspot') == '#dc3545'   # Red
    
    def test_heatmap_data_includes_all_puroks(self, setup_database, sample_incidents):
        """FR-4.1: Test that heatmap includes all puroks even with 0 incidents."""
        data = AnalyticsModel.get_incident_count_by_purok(days_back=30)
        
        # Get total purok count
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM purok")
        total_puroks = cursor.fetchone()[0]
        conn.close()
        
        assert len(data) == total_puroks
    
    def test_heatmap_date_filtering(self, setup_database, sample_incidents):
        """FR-4.1: Test that heatmap respects date range."""
        # Data from last 7 days vs last 30 days should potentially differ
        data_7 = AnalyticsModel.get_incident_count_by_purok(days_back=7)
        data_30 = AnalyticsModel.get_incident_count_by_purok(days_back=30)
        
        assert isinstance(data_7, list)
        assert isinstance(data_30, list)
        
        # Sum of incidents in 30 days should be >= 7 days
        sum_7 = sum(d['incident_count'] for d in data_7)
        sum_30 = sum(d['incident_count'] for d in data_30)
        assert sum_30 >= sum_7


# ============================================
# ANALYTICS MODEL TESTS - FR-4.2 Time Analysis
# ============================================

class TestTimeAnalysis:
    """Test Time-Series Analysis functionality (FR-4.2)."""
    
    def test_get_incidents_by_time_of_day(self, setup_database, sample_incidents):
        """FR-4.2: Test getting incidents by hour of day."""
        data = AnalyticsModel.get_incidents_by_time_of_day(days_back=30)
        
        assert isinstance(data, list)
        assert len(data) == 24  # All 24 hours
        
        # Verify structure
        first_item = data[0]
        assert 'hour' in first_item
        assert 'incident_count' in first_item
        assert 'time_label' in first_item
        assert 'period' in first_item
    
    def test_all_hours_represented(self, setup_database, sample_incidents):
        """FR-4.2: Test that all 24 hours are in the result."""
        data = AnalyticsModel.get_incidents_by_time_of_day(days_back=30)
        
        hours = [d['hour'] for d in data]
        assert hours == list(range(24))
    
    def test_time_label_format(self, setup_database):
        """FR-4.2: Test time label formatting."""
        assert AnalyticsModel._format_hour(0) == "12:00 AM"
        assert AnalyticsModel._format_hour(6) == "6:00 AM"
        assert AnalyticsModel._format_hour(12) == "12:00 PM"
        assert AnalyticsModel._format_hour(18) == "6:00 PM"
        assert AnalyticsModel._format_hour(23) == "11:00 PM"
    
    def test_time_period_classification(self, setup_database):
        """FR-4.2: Test time period classification."""
        assert AnalyticsModel._get_time_period(6) == "Morning"
        assert AnalyticsModel._get_time_period(11) == "Morning"
        assert AnalyticsModel._get_time_period(12) == "Afternoon"
        assert AnalyticsModel._get_time_period(17) == "Afternoon"
        assert AnalyticsModel._get_time_period(18) == "Evening"
        assert AnalyticsModel._get_time_period(21) == "Evening"
        assert AnalyticsModel._get_time_period(22) == "Night"
        assert AnalyticsModel._get_time_period(3) == "Night"
    
    def test_get_most_dangerous_hours(self, setup_database, sample_incidents):
        """FR-4.2: Test getting most dangerous hours."""
        data = AnalyticsModel.get_most_dangerous_hours(days_back=30, top_n=3)
        
        assert isinstance(data, list)
        assert len(data) <= 3
        
        # Should be sorted by incident count descending
        if len(data) > 1:
            assert data[0]['incident_count'] >= data[1]['incident_count']
    
    def test_get_incidents_by_day_of_week(self, setup_database, sample_incidents):
        """FR-4.2: Test getting incidents by day of week."""
        data = AnalyticsModel.get_incidents_by_day_of_week(days_back=30)
        
        assert isinstance(data, list)
        assert len(data) == 7  # All 7 days
        
        # Verify day names
        day_names = [d['day_name'] for d in data]
        assert 'Sunday' in day_names
        assert 'Monday' in day_names
        assert 'Saturday' in day_names


# ============================================
# ANALYTICS MODEL TESTS - FR-4.3 Patrol Recommender
# ============================================

class TestPatrolRecommender:
    """Test Patrol Recommender functionality (FR-4.3)."""
    
    def test_generate_patrol_recommendations(self, setup_database, sample_incidents):
        """FR-4.3: Test generating patrol recommendations."""
        recommendations = AnalyticsModel.generate_patrol_recommendations(days_back=30)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_recommendation_structure(self, setup_database, sample_incidents):
        """FR-4.3: Test recommendation data structure."""
        recommendations = AnalyticsModel.generate_patrol_recommendations(days_back=30)
        
        rec = recommendations[0]
        assert 'priority' in rec
        assert 'purok_name' in rec
        assert 'time_range' in rec
        assert 'reason' in rec
        assert 'severity_level' in rec
    
    def test_recommendations_prioritized(self, setup_database, sample_incidents):
        """FR-4.3: Test that recommendations are prioritized."""
        recommendations = AnalyticsModel.generate_patrol_recommendations(days_back=30)
        
        priorities = [r['priority'] for r in recommendations]
        # Priorities should be sequential starting from 1
        assert priorities[0] == 1
        for i in range(1, len(priorities)):
            assert priorities[i] > priorities[i-1]
    
    def test_recommendations_with_no_data(self, setup_database):
        """FR-4.3: Test recommendations when no incidents exist."""
        # Query with very old date range where no data exists
        recommendations = AnalyticsModel.generate_patrol_recommendations(days_back=1)
        
        assert isinstance(recommendations, list)
        # Should still return default recommendation
        assert len(recommendations) >= 1
    
    def test_recommendation_includes_time_range(self, setup_database, sample_incidents):
        """FR-4.3: Test that recommendations include time ranges."""
        recommendations = AnalyticsModel.generate_patrol_recommendations(days_back=30)
        
        for rec in recommendations:
            assert 'time_range' in rec
            # Time range should contain AM/PM format
            assert 'AM' in rec['time_range'] or 'PM' in rec['time_range']


# ============================================
# ANALYTICS CONTROLLER TESTS
# ============================================

class TestAnalyticsController:
    """Test Analytics Controller operations."""
    
    def test_get_crime_heatmap_data(self, setup_database, sample_incidents):
        """Test getting heatmap data via controller."""
        success, message, data = AnalyticsController.get_crime_heatmap_data(days_back=30)
        
        assert success is True
        assert data is not None
        assert isinstance(data, list)
    
    def test_get_time_analysis_data(self, setup_database, sample_incidents):
        """Test getting time analysis data via controller."""
        success, message, data = AnalyticsController.get_time_analysis_data(days_back=30)
        
        assert success is True
        assert data is not None
        assert 'hourly_distribution' in data
        assert 'daily_distribution' in data
        assert 'most_dangerous_hours' in data
        assert 'period_summary' in data
    
    def test_get_patrol_recommendations(self, setup_database, sample_incidents):
        """Test getting patrol recommendations via controller."""
        success, message, data = AnalyticsController.get_patrol_recommendations(days_back=30)
        
        assert success is True
        assert data is not None
        assert isinstance(data, list)
    
    def test_format_patrol_report(self, setup_database, sample_incidents):
        """Test formatting patrol report."""
        recommendations = AnalyticsModel.generate_patrol_recommendations(days_back=30)
        report = AnalyticsController.format_patrol_report(recommendations)
        
        assert isinstance(report, str)
        assert "PATROL DEPLOYMENT RECOMMENDATIONS" in report
        assert "Priority #1" in report
    
    def test_get_dashboard_data(self, setup_database, sample_incidents):
        """Test getting comprehensive dashboard data."""
        success, message, data = AnalyticsController.get_dashboard_data(days_back=30)
        
        assert success is True
        assert data is not None
        assert 'summary' in data
        assert 'purok_heatmap' in data
        assert 'incident_types' in data
        assert 'patrol_recommendations' in data
    
    def test_dashboard_summary_contents(self, setup_database, sample_incidents):
        """Test dashboard summary contains expected fields."""
        success, _, data = AnalyticsController.get_dashboard_data(days_back=30)
        
        summary = data['summary']
        assert 'total_incidents' in summary
        assert 'pending_cases' in summary
        assert 'hotspot_count' in summary
        assert 'caution_count' in summary
        assert 'safe_count' in summary


# ============================================
# CHART GENERATION TESTS
# ============================================

class TestChartGeneration:
    """Test chart generation functionality."""
    
    def test_generate_heatmap_bar_chart(self, setup_database, sample_incidents, temp_output_dir):
        """Test generating heatmap bar chart."""
        output_path = os.path.join(temp_output_dir, "heatmap_bar.png")
        success, message, path = AnalyticsController.generate_heatmap_chart(
            days_back=30,
            output_path=output_path,
            chart_type='bar'
        )
        
        # May fail if matplotlib not available
        if success:
            assert path is not None
            assert os.path.exists(path)
    
    def test_generate_heatmap_pie_chart(self, setup_database, sample_incidents, temp_output_dir):
        """Test generating heatmap pie chart."""
        output_path = os.path.join(temp_output_dir, "heatmap_pie.png")
        success, message, path = AnalyticsController.generate_heatmap_chart(
            days_back=30,
            output_path=output_path,
            chart_type='pie'
        )
        
        if success:
            assert path is not None
            assert os.path.exists(path)
    
    def test_generate_time_chart(self, setup_database, sample_incidents, temp_output_dir):
        """Test generating time analysis chart."""
        output_path = os.path.join(temp_output_dir, "time_analysis.png")
        success, message, path = AnalyticsController.generate_time_chart(
            days_back=30,
            output_path=output_path
        )
        
        if success:
            assert path is not None
            assert os.path.exists(path)


# ============================================
# ADDITIONAL ANALYTICS TESTS
# ============================================

class TestAdditionalAnalytics:
    """Test additional analytics functionality."""
    
    def test_get_incidents_by_type(self, setup_database, sample_incidents):
        """Test getting incidents by incident type."""
        data = AnalyticsModel.get_incidents_by_type(days_back=30)
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify structure
        first_item = data[0]
        assert 'type_id' in first_item
        assert 'type_name' in first_item
        assert 'incident_count' in first_item
    
    def test_get_monthly_trend(self, setup_database, sample_incidents):
        """Test getting monthly trend data."""
        data = AnalyticsModel.get_monthly_trend(months_back=6)
        
        assert isinstance(data, list)
        
        if len(data) > 0:
            item = data[0]
            assert 'year' in item
            assert 'month' in item
            assert 'month_name' in item
            assert 'incident_count' in item
    
    def test_export_analytics_report(self, setup_database, sample_incidents, temp_output_dir):
        """Test exporting analytics report."""
        output_path = os.path.join(temp_output_dir, "analytics_report.txt")
        success, message, path = AnalyticsController.export_analytics_report(
            days_back=30,
            output_path=output_path,
            include_charts=False
        )
        
        assert success is True
        assert path is not None
        assert os.path.exists(path)
        
        # Verify content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "KALASAG" in content
            assert "CRIME ANALYTICS REPORT" in content


# ============================================
# INTEGRATION TESTS
# ============================================

class TestAnalyticsIntegration:
    """Integration tests for analytics workflow."""
    
    def test_full_analytics_workflow(self, setup_database, sample_incidents):
        """Test complete analytics workflow."""
        # 1. Get heatmap data
        success, _, heatmap = AnalyticsController.get_crime_heatmap_data(30)
        assert success is True
        
        # Find hotspot areas
        hotspots = [p for p in heatmap if p['severity_level'] == 'hotspot']
        
        # 2. Get time analysis
        success, _, time_data = AnalyticsController.get_time_analysis_data(30)
        assert success is True
        
        dangerous_hours = time_data['most_dangerous_hours']
        
        # 3. Get patrol recommendations
        success, _, recommendations = AnalyticsController.get_patrol_recommendations(30)
        assert success is True
        
        # 4. Recommendations should reference hotspot locations
        if hotspots and recommendations:
            hotspot_names = [h['purok_name'] for h in hotspots]
            rec_locations = [r['purok_name'] for r in recommendations]
            # At least one hotspot should be in recommendations
            overlap = set(hotspot_names) & set(rec_locations)
            assert len(overlap) > 0 or len(hotspots) == 0
    
    def test_dashboard_data_consistency(self, setup_database, sample_incidents):
        """Test that dashboard data is internally consistent."""
        success, _, dashboard = AnalyticsController.get_dashboard_data(30)
        assert success is True
        
        summary = dashboard['summary']
        heatmap = dashboard['purok_heatmap']
        
        # Hotspot counts should match
        calculated_hotspots = len([p for p in heatmap if p['severity_level'] == 'hotspot'])
        assert summary['hotspot_count'] == calculated_hotspots
        
        calculated_caution = len([p for p in heatmap if p['severity_level'] == 'caution'])
        assert summary['caution_count'] == calculated_caution


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
