"""
KALASAG - Test Suite for Blotter Module
TDD tests for E-Blotter & Case Management.
Tests FR-2.1, FR-2.2, FR-2.3, FR-2.4
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from database import init_database, seed_default_data
from models.blotter import BlotterCaseModel, CaseInvolvementModel, IncidentTypeModel
from models.resident import ResidentModel, PurokModel
from controllers.blotter_controller import BlotterController, IncidentTypeController


# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="module")
def setup_database():
    """Set up test database."""
    # Use a test database
    database.DATABASE_PATH = "test_kalasag_blotter.db"
    
    # Remove existing test database
    if os.path.exists("test_kalasag_blotter.db"):
        os.remove("test_kalasag_blotter.db")
    
    init_database()
    seed_default_data()
    
    yield
    
    # Cleanup
    if os.path.exists("test_kalasag_blotter.db"):
        os.remove("test_kalasag_blotter.db")


@pytest.fixture
def sample_resident(setup_database):
    """Create a sample resident for testing."""
    res_id = ResidentModel.create(
        first_name="Test",
        last_name="Resident",
        sex="Male"
    )
    return res_id


@pytest.fixture
def sample_respondent(setup_database):
    """Create a sample respondent for testing."""
    res_id = ResidentModel.create(
        first_name="Suspect",
        last_name="Person",
        sex="Male"
    )
    return res_id


@pytest.fixture
def sample_blotter_data(sample_resident, sample_respondent):
    """Sample valid blotter case data."""
    return {
        "date_time": datetime.now().isoformat(),
        "narrative": "This is a detailed description of the incident that occurred. "
                    "The complainant reported that the respondent was involved in a disturbance.",
        "purok_id": 1,
        "type_id": 1,
        "complainants": [sample_resident],
        "respondents": [sample_respondent]
    }


# ============================================
# INCIDENT TYPE MODEL TESTS
# ============================================

class TestIncidentTypeModel:
    """Test Incident Type operations."""
    
    def test_get_all_incident_types(self, setup_database):
        """Test retrieving all incident types (seeded data)."""
        types = IncidentTypeModel.get_all()
        
        assert isinstance(types, list)
        assert len(types) > 0  # Default seed data exists
    
    def test_get_incident_type_by_id(self, setup_database):
        """Test retrieving incident type by ID."""
        types = IncidentTypeModel.get_all()
        if types:
            incident_type = IncidentTypeModel.get_by_id(types[0]['type_id'])
            assert incident_type is not None
            assert 'name' in incident_type
            assert 'severity' in incident_type
    
    def test_create_incident_type(self, setup_database):
        """Test creating a new incident type."""
        type_id = IncidentTypeModel.create(
            name="Test Incident",
            severity=3,
            description="A test incident type"
        )
        
        assert type_id is not None
        assert type_id > 0
        
        # Verify
        incident_type = IncidentTypeModel.get_by_id(type_id)
        assert incident_type['name'] == "Test Incident"
        assert incident_type['severity'] == 3
    
    def test_create_incident_type_invalid_severity(self, setup_database):
        """Test creating incident type with invalid severity."""
        with pytest.raises(ValueError):
            IncidentTypeModel.create(name="Bad Type", severity=10)
        
        with pytest.raises(ValueError):
            IncidentTypeModel.create(name="Bad Type", severity=0)


# ============================================
# BLOTTER CASE MODEL TESTS
# ============================================

class TestBlotterCaseModel:
    """Test Blotter Case CRUD operations."""
    
    def test_create_blotter_case(self, setup_database, sample_blotter_data):
        """FR-2.1: Test creating a blotter case with incident details."""
        case_id, case_number = BlotterCaseModel.create(
            date_time=sample_blotter_data['date_time'],
            narrative=sample_blotter_data['narrative'],
            purok_id=sample_blotter_data['purok_id'],
            type_id=sample_blotter_data['type_id'],
            complainants=sample_blotter_data['complainants'],
            respondents=sample_blotter_data['respondents']
        )
        
        assert case_id is not None
        assert case_id > 0
        assert case_number is not None
        assert case_number.startswith("BLT-")
    
    def test_case_number_format(self, setup_database):
        """Test that case numbers follow the correct format."""
        case_id, case_number = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test narrative for case number format verification test."
        )
        
        # Format: BLT-YYYYMM-XXXX
        year_month = datetime.now().strftime("%Y%m")
        assert case_number.startswith(f"BLT-{year_month}-")
    
    def test_get_blotter_case_by_id(self, setup_database):
        """Test retrieving a blotter case by ID."""
        case_id, case_number = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for retrieval testing in the blotter module."
        )
        
        case = BlotterCaseModel.get_by_id(case_id)
        
        assert case is not None
        assert case['case_id'] == case_id
        assert case['case_number'] == case_number
        assert case['status'] == 'Pending'  # Default status
    
    def test_get_blotter_case_by_case_number(self, setup_database):
        """Test retrieving a blotter case by case number."""
        case_id, case_number = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for case number retrieval testing module."
        )
        
        case = BlotterCaseModel.get_by_case_number(case_number)
        
        assert case is not None
        assert case['case_id'] == case_id
    
    def test_case_with_involvements(self, setup_database, sample_resident, sample_respondent):
        """FR-2.2: Test linking residents to cases as complainant/respondent."""
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case with complainant and respondent linked to resident profiles.",
            complainants=[sample_resident],
            respondents=[sample_respondent]
        )
        
        case = BlotterCaseModel.get_by_id(case_id)
        
        assert len(case['complainants']) == 1
        assert len(case['respondents']) == 1
        assert case['complainants'][0]['res_id'] == sample_resident
        assert case['respondents'][0]['res_id'] == sample_respondent
    
    def test_update_case_status_pending_to_settlement(self, setup_database):
        """FR-2.3: Test updating case status to Amicable Settlement."""
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for status update from pending to amicable settlement."
        )
        
        success = BlotterCaseModel.update_status(case_id, "Amicable Settlement")
        assert success is True
        
        case = BlotterCaseModel.get_by_id(case_id)
        assert case['status'] == "Amicable Settlement"
    
    def test_update_case_status_to_escalated(self, setup_database):
        """FR-2.3: Test updating case status to Escalated to PNP."""
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for escalation to PNP status update testing."
        )
        
        success = BlotterCaseModel.update_status(case_id, "Escalated to PNP")
        assert success is True
        
        case = BlotterCaseModel.get_by_id(case_id)
        assert case['status'] == "Escalated to PNP"
    
    def test_update_case_status_to_closed(self, setup_database):
        """FR-2.3: Test updating case status to Closed."""
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for closing status update testing in the system."
        )
        
        success = BlotterCaseModel.update_status(case_id, "Closed")
        assert success is True
        
        case = BlotterCaseModel.get_by_id(case_id)
        assert case['status'] == "Closed"
    
    def test_update_case_status_invalid(self, setup_database):
        """FR-2.3: Test updating case status with invalid value."""
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for invalid status update testing error handling."
        )
        
        with pytest.raises(ValueError):
            BlotterCaseModel.update_status(case_id, "InvalidStatus")
    
    def test_search_cases(self, setup_database):
        """Test searching cases by narrative."""
        unique_keyword = f"UNIQUESEARCH{datetime.now().timestamp()}"
        
        case_id, case_number = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative=f"This case contains {unique_keyword} for search testing purposes."
        )
        
        results = BlotterCaseModel.search(unique_keyword)
        
        assert len(results) > 0
        assert any(r['case_id'] == case_id for r in results)
    
    def test_filter_by_status(self, setup_database):
        """Test filtering cases by status."""
        # Create a pending case
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test pending case for status filtering in the blotter module."
        )
        
        pending_cases = BlotterCaseModel.get_all(status='Pending')
        
        assert all(c['status'] == 'Pending' for c in pending_cases)
    
    def test_filter_by_date_range(self, setup_database):
        """Test filtering cases by date range."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        cases = BlotterCaseModel.get_all(start_date=today, end_date=today)
        
        # All returned cases should be from today
        for case in cases:
            case_date = case['date_time'][:10]
            assert case_date == today
    
    def test_get_cases_by_resident(self, setup_database, sample_resident):
        """Test getting all cases involving a specific resident."""
        # Create case with this resident
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for resident involvement query testing module.",
            complainants=[sample_resident]
        )
        
        cases = BlotterCaseModel.get_cases_by_resident(sample_resident)
        
        assert len(cases) > 0
        assert any(c['case_id'] == case_id for c in cases)
    
    def test_get_statistics(self, setup_database):
        """Test getting blotter statistics."""
        stats = BlotterCaseModel.get_statistics()
        
        assert 'total_cases' in stats
        assert 'by_status' in stats
        assert 'by_purok' in stats
        assert 'by_type' in stats
        assert 'pending_count' in stats


# ============================================
# CASE INVOLVEMENT MODEL TESTS
# ============================================

class TestCaseInvolvementModel:
    """Test Case Involvement operations."""
    
    def test_add_involvement(self, setup_database, sample_resident):
        """FR-2.2: Test adding a resident to a case."""
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for adding involvement after case creation test."
        )
        
        link_id = CaseInvolvementModel.add_involvement(
            case_id=case_id,
            res_id=sample_resident,
            role='Witness'
        )
        
        assert link_id is not None
        assert link_id > 0
    
    def test_add_involvement_invalid_role(self, setup_database, sample_resident):
        """Test adding involvement with invalid role."""
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for invalid role testing in case involvement."
        )
        
        with pytest.raises(ValueError):
            CaseInvolvementModel.add_involvement(case_id, sample_resident, 'InvalidRole')
    
    def test_remove_involvement(self, setup_database, sample_resident):
        """Test removing a resident from a case."""
        case_id, _ = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Test case for removing involvement testing in the system.",
            witnesses=[sample_resident]
        )
        
        success = CaseInvolvementModel.remove_involvement(
            case_id=case_id,
            res_id=sample_resident,
            role='Witness'
        )
        
        assert success is True
        
        # Verify removed
        case = BlotterCaseModel.get_by_id(case_id)
        assert len(case['witnesses']) == 0
    
    def test_check_recidivist_no_prior(self, setup_database):
        """FR-2.4: Test recidivist check for resident with no prior cases."""
        # Create a new resident with no cases
        res_id = ResidentModel.create(
            first_name="Clean",
            last_name="Record"
        )
        
        result = CaseInvolvementModel.check_recidivist(res_id)
        
        assert result['is_recidivist'] is False
        assert result['prior_cases'] == 0
        assert result['case_numbers'] == []
    
    def test_check_recidivist_with_prior(self, setup_database):
        """FR-2.4: Test recidivist check for resident with prior cases as respondent."""
        # Create a resident
        res_id = ResidentModel.create(
            first_name="Repeat",
            last_name="Offender"
        )
        
        # Create a case with this resident as respondent
        case_id, case_number = BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="First offense case for recidivist testing in the blotter module.",
            respondents=[res_id]
        )
        
        # Check recidivism
        result = CaseInvolvementModel.check_recidivist(res_id)
        
        assert result['is_recidivist'] is True
        assert result['prior_cases'] == 1
        assert case_number in result['case_numbers']
    
    def test_check_recidivist_complainant_not_counted(self, setup_database):
        """FR-2.4: Test that complainant roles don't count as recidivism."""
        # Create a resident
        res_id = ResidentModel.create(
            first_name="Frequent",
            last_name="Complainant"
        )
        
        # Create a case with this resident as complainant (not respondent)
        BlotterCaseModel.create(
            date_time=datetime.now().isoformat(),
            narrative="Case where resident is complainant, not respondent test.",
            complainants=[res_id]
        )
        
        # Check recidivism - should be false since only respondent roles count
        result = CaseInvolvementModel.check_recidivist(res_id)
        
        assert result['is_recidivist'] is False


# ============================================
# BLOTTER CONTROLLER TESTS
# ============================================

class TestBlotterController:
    """Test Blotter Controller operations."""
    
    def test_validate_blotter_data_valid(self, sample_blotter_data):
        """Test validation with valid data."""
        controller = BlotterController()
        
        is_valid, errors = controller.validate_blotter_data(sample_blotter_data)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_blotter_data_missing_narrative(self):
        """Test validation with missing narrative."""
        controller = BlotterController()
        
        data = {
            "date_time": datetime.now().isoformat(),
            "narrative": "",
            "complainants": [1]
        }
        
        is_valid, errors = controller.validate_blotter_data(data)
        
        assert is_valid is False
        assert any("Narrative" in e for e in errors)
    
    def test_validate_blotter_data_future_date(self):
        """Test validation with future date."""
        controller = BlotterController()
        
        future_date = (datetime.now() + timedelta(days=10)).isoformat()
        
        data = {
            "date_time": future_date,
            "narrative": "This is a valid narrative for testing future date validation.",
            "complainants": [1]
        }
        
        is_valid, errors = controller.validate_blotter_data(data)
        
        assert is_valid is False
        assert any("future" in e.lower() for e in errors)
    
    def test_validate_blotter_data_no_parties(self):
        """Test validation with no complainants or respondents."""
        controller = BlotterController()
        
        data = {
            "date_time": datetime.now().isoformat(),
            "narrative": "This is a valid narrative but no parties are specified."
        }
        
        is_valid, errors = controller.validate_blotter_data(data)
        
        assert is_valid is False
        assert any("complainant" in e.lower() or "respondent" in e.lower() for e in errors)
    
    def test_create_blotter_via_controller(self, setup_database, sample_blotter_data):
        """Test creating blotter case through controller."""
        controller = BlotterController(current_user_id=1)
        
        success, result = controller.create_blotter_case(sample_blotter_data)
        
        assert success is True
        assert 'case_id' in result
        assert 'case_number' in result
        assert 'recidivist_alerts' in result
    
    def test_recidivist_alert_on_create(self, setup_database):
        """FR-2.4: Test recidivist alert when creating case with repeat offender."""
        controller = BlotterController(current_user_id=1)
        
        # Create a repeat offender
        offender_id = ResidentModel.create(
            first_name="Serial",
            last_name="Troublemaker"
        )
        
        complainant_id = ResidentModel.create(
            first_name="Innocent",
            last_name="Victim"
        )
        
        # First case
        first_data = {
            "date_time": datetime.now().isoformat(),
            "narrative": "First incident involving the serial troublemaker resident test.",
            "complainants": [complainant_id],
            "respondents": [offender_id]
        }
        controller.create_blotter_case(first_data)
        
        # Second case with same offender - should trigger alert
        second_data = {
            "date_time": datetime.now().isoformat(),
            "narrative": "Second incident involving the same serial troublemaker test.",
            "complainants": [complainant_id],
            "respondents": [offender_id]
        }
        
        success, result = controller.create_blotter_case(second_data)
        
        assert success is True
        assert len(result['recidivist_alerts']) > 0
        assert any(a['res_id'] == offender_id for a in result['recidivist_alerts'])
    
    def test_update_status_via_controller(self, setup_database):
        """FR-2.3: Test updating status through controller."""
        controller = BlotterController(current_user_id=1)
        
        # Create a case first
        res_id = ResidentModel.create(first_name="Status", last_name="Test")
        data = {
            "date_time": datetime.now().isoformat(),
            "narrative": "Test case for controller status update testing module.",
            "complainants": [res_id]
        }
        success, result = controller.create_blotter_case(data)
        case_id = result['case_id']
        
        # Update status
        success, _ = controller.update_case_status(case_id, "Closed")
        
        assert success is True
        
        # Verify
        case = controller.get_blotter_case(case_id)
        assert case['status'] == "Closed"
    
    def test_get_pending_cases(self, setup_database):
        """Test getting all pending cases."""
        controller = BlotterController()
        
        pending = controller.get_pending_cases()
        
        assert all(c['status'] == 'Pending' for c in pending)
    
    def test_get_statistics_via_controller(self, setup_database):
        """Test getting statistics through controller."""
        controller = BlotterController()
        
        stats = controller.get_statistics()
        
        assert 'total_cases' in stats
        assert 'by_status' in stats
        assert 'pending_count' in stats


# ============================================
# INCIDENT TYPE CONTROLLER TESTS
# ============================================

class TestIncidentTypeController:
    """Test Incident Type Controller operations."""
    
    def test_get_all_incident_types(self, setup_database):
        """Test getting all incident types."""
        types = IncidentTypeController.get_all()
        
        assert isinstance(types, list)
        assert len(types) > 0
    
    def test_create_incident_type_via_controller(self, setup_database):
        """Test creating incident type through controller."""
        success, result = IncidentTypeController.create(
            name="Controller Test Type",
            severity=2,
            description="Created via controller"
        )
        
        assert success is True
        assert isinstance(result, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
