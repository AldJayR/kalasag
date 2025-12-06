"""
KALASAG - Test Suite for Resident Module
TDD tests for Resident and Household operations.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_database, get_connection, DATABASE_PATH
from models.resident import ResidentModel, HouseholdModel, PurokModel
from controllers.resident_controller import ResidentController
from utils.validators import (
    validate_name, validate_birthdate, validate_sex,
    validate_civil_status, validate_contact_number
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="module")
def setup_database():
    """Set up test database."""
    # Use a test database
    global DATABASE_PATH
    import database
    database.DATABASE_PATH = "test_kalasag.db"
    
    # Initialize fresh database
    if os.path.exists("test_kalasag.db"):
        os.remove("test_kalasag.db")
    
    init_database()
    
    # Seed default data (puroks, incident types, admin user)
    from database import seed_default_data
    seed_default_data()
    
    yield
    
    # Cleanup
    if os.path.exists("test_kalasag.db"):
        os.remove("test_kalasag.db")


@pytest.fixture
def sample_resident_data():
    """Sample valid resident data."""
    return {
        "first_name": "Juan",
        "middle_name": "Santos",
        "last_name": "Dela Cruz",
        "alias": "Jojo",
        "birthdate": "1990-05-15",
        "sex": "Male",
        "civil_status": "Single",
        "occupation": "Farmer",
        "contact_number": "09171234567",
        "is_indigent": False,
        "status": "Active"
    }


@pytest.fixture
def sample_household_data():
    """Sample valid household data."""
    return {
        "house_number": "123",
        "street_name": "Rizal Street"
    }


# ============================================
# VALIDATOR TESTS
# ============================================

class TestValidators:
    """Test input validation functions."""
    
    def test_validate_name_valid(self):
        """Test valid names."""
        assert validate_name("Juan")[0] is True
        assert validate_name("Maria Clara")[0] is True
        assert validate_name("Dela Cruz")[0] is True
        assert validate_name("O'Brien")[0] is True
        assert validate_name("José Rizal")[0] is True  # With ñ variant
    
    def test_validate_name_invalid(self):
        """Test invalid names."""
        assert validate_name("")[0] is False
        assert validate_name("A")[0] is False  # Too short
        assert validate_name("Juan123")[0] is False  # Numbers
        assert validate_name("Juan@Cruz")[0] is False  # Special chars
    
    def test_validate_birthdate_valid(self):
        """Test valid birthdates."""
        assert validate_birthdate("1990-05-15")[0] is True
        assert validate_birthdate("2000-01-01")[0] is True
        assert validate_birthdate("")[0] is True  # Empty allowed
    
    def test_validate_birthdate_invalid(self):
        """Test invalid birthdates."""
        assert validate_birthdate("2030-01-01")[0] is False  # Future
        assert validate_birthdate("1800-01-01")[0] is False  # Too old
        assert validate_birthdate("not-a-date")[0] is False
        assert validate_birthdate("05-15-1990")[0] is False  # Wrong format
    
    def test_validate_sex(self):
        """Test sex validation."""
        assert validate_sex("Male")[0] is True
        assert validate_sex("Female")[0] is True
        assert validate_sex("")[0] is True  # Empty allowed
        assert validate_sex("Other")[0] is False
    
    def test_validate_civil_status(self):
        """Test civil status validation."""
        assert validate_civil_status("Single")[0] is True
        assert validate_civil_status("Married")[0] is True
        assert validate_civil_status("Widowed")[0] is True
        assert validate_civil_status("")[0] is True
        assert validate_civil_status("Complicated")[0] is False
    
    def test_validate_contact_number(self):
        """Test Philippine contact number validation."""
        assert validate_contact_number("09171234567")[0] is True
        assert validate_contact_number("+639171234567")[0] is True
        assert validate_contact_number("639171234567")[0] is True
        assert validate_contact_number("")[0] is True
        assert validate_contact_number("1234567")[0] is False  # Too short
        assert validate_contact_number("abc123")[0] is False


# ============================================
# HOUSEHOLD MODEL TESTS
# ============================================

class TestHouseholdModel:
    """Test Household CRUD operations."""
    
    def test_create_household(self, setup_database, sample_household_data):
        """Test creating a household."""
        hh_id = HouseholdModel.create(
            house_number=sample_household_data["house_number"],
            street_name=sample_household_data["street_name"]
        )
        
        assert hh_id is not None
        assert hh_id > 0
    
    def test_get_household(self, setup_database):
        """Test retrieving a household."""
        # Create first
        hh_id = HouseholdModel.create("456", "Mabini Street")
        
        # Retrieve
        household = HouseholdModel.get_by_id(hh_id)
        
        assert household is not None
        assert household["house_number"] == "456"
        assert household["street_name"] == "Mabini Street"
    
    def test_update_household(self, setup_database):
        """Test updating a household."""
        hh_id = HouseholdModel.create("789", "Bonifacio Street")
        
        success = HouseholdModel.update(hh_id, house_number="999")
        assert success is True
        
        updated = HouseholdModel.get_by_id(hh_id)
        assert updated["house_number"] == "999"
    
    def test_get_all_households(self, setup_database):
        """Test getting all households."""
        households = HouseholdModel.get_all()
        
        assert isinstance(households, list)
        assert len(households) > 0


# ============================================
# RESIDENT MODEL TESTS
# ============================================

class TestResidentModel:
    """Test Resident CRUD operations (FR-1.1, FR-1.2, FR-1.3, FR-1.4)."""
    
    def test_create_resident(self, setup_database, sample_resident_data):
        """FR-1.1: Test creating a resident profile."""
        res_id = ResidentModel.create(**sample_resident_data)
        
        assert res_id is not None
        assert res_id > 0
    
    def test_get_resident(self, setup_database):
        """Test retrieving a resident by ID."""
        res_id = ResidentModel.create(
            first_name="Maria",
            last_name="Santos",
            sex="Female"
        )
        
        resident = ResidentModel.get_by_id(res_id)
        
        assert resident is not None
        assert resident["first_name"] == "Maria"
        assert resident["last_name"] == "Santos"
    
    def test_resident_with_household(self, setup_database):
        """FR-1.2: Test grouping resident under household."""
        # Create household
        hh_id = HouseholdModel.create("100", "Test Street")
        
        # Create resident with household
        res_id = ResidentModel.create(
            first_name="Pedro",
            last_name="Garcia",
            hh_id=hh_id
        )
        
        resident = ResidentModel.get_by_id(res_id)
        assert resident["hh_id"] == hh_id
        
        # Check household members
        members = HouseholdModel.get_members(hh_id)
        assert any(m["res_id"] == res_id for m in members)
    
    def test_search_by_name(self, setup_database):
        """FR-1.3: Test search by name."""
        # Create test resident
        ResidentModel.create(
            first_name="Unique",
            last_name="Searchname"
        )
        
        results = ResidentModel.search("Searchname", "name")
        
        assert len(results) > 0
        assert any(r["last_name"] == "Searchname" for r in results)
    
    def test_search_by_alias(self, setup_database):
        """FR-1.3: Test search by alias."""
        ResidentModel.create(
            first_name="Test",
            last_name="Person",
            alias="UniqueAlias123"
        )
        
        results = ResidentModel.search("UniqueAlias123", "alias")
        
        assert len(results) > 0
        assert any(r["alias"] == "UniqueAlias123" for r in results)
    
    def test_update_status(self, setup_database):
        """FR-1.4: Test updating resident status."""
        res_id = ResidentModel.create(
            first_name="Status",
            last_name="Test"
        )
        
        # Update to Deceased
        success = ResidentModel.update_status(res_id, "Deceased")
        assert success is True
        
        resident = ResidentModel.get_by_id(res_id)
        assert resident["status"] == "Deceased"
        
        # Update to Moved Out
        success = ResidentModel.update_status(res_id, "Moved Out")
        assert success is True
        
        resident = ResidentModel.get_by_id(res_id)
        assert resident["status"] == "Moved Out"
    
    def test_update_indigent_status(self, setup_database):
        """FR-1.4: Test updating indigent status."""
        res_id = ResidentModel.create(
            first_name="Indigent",
            last_name="Test",
            is_indigent=False
        )
        
        success = ResidentModel.update_indigent_status(res_id, True)
        assert success is True
        
        resident = ResidentModel.get_by_id(res_id)
        assert resident["is_indigent"] == 1
    
    def test_filter_by_status(self, setup_database):
        """Test filtering residents by status."""
        # Create active resident
        ResidentModel.create(
            first_name="Active",
            last_name="Person",
            status="Active"
        )
        
        active_residents = ResidentModel.get_all(status="Active")
        
        assert all(r["status"] == "Active" for r in active_residents)
    
    def test_filter_by_indigent(self, setup_database):
        """Test filtering residents by indigent status."""
        ResidentModel.create(
            first_name="Poor",
            last_name="Person",
            is_indigent=True
        )
        
        indigent_residents = ResidentModel.get_all(is_indigent=True)
        
        assert all(r["is_indigent"] == 1 for r in indigent_residents)
    
    def test_get_statistics(self, setup_database):
        """Test resident statistics."""
        stats = ResidentModel.get_statistics()
        
        assert "total_active" in stats
        assert "by_status" in stats
        assert "indigent_count" in stats
        assert "by_purok" in stats


# ============================================
# CONTROLLER TESTS
# ============================================

class TestResidentController:
    """Test Resident Controller operations."""
    
    def test_validate_resident_data_valid(self):
        """Test validation with valid data."""
        controller = ResidentController()
        
        data = {
            "first_name": "Juan",
            "last_name": "Cruz",
            "birthdate": "1990-01-01",
            "sex": "Male"
        }
        
        is_valid, errors = controller.validate_resident_data(data)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_resident_data_invalid(self):
        """Test validation with invalid data."""
        controller = ResidentController()
        
        data = {
            "first_name": "",  # Required but empty
            "last_name": "123",  # Invalid characters
            "birthdate": "2030-01-01",  # Future date
            "sex": "Unknown"  # Invalid value
        }
        
        is_valid, errors = controller.validate_resident_data(data)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_create_resident_via_controller(self, setup_database):
        """Test creating resident through controller."""
        controller = ResidentController(current_user_id=1)
        
        data = {
            "first_name": "Controller",
            "last_name": "Test",
            "sex": "Male"
        }
        
        success, result = controller.create_resident(data)
        
        assert success is True
        assert isinstance(result, int)  # res_id
    
    def test_search_residents_via_controller(self, setup_database):
        """Test search through controller."""
        controller = ResidentController()
        
        # Create a resident to search for
        controller.create_resident({
            "first_name": "Searchable",
            "last_name": "ViaController"
        })
        
        results = controller.search_residents("ViaController")
        
        assert len(results) > 0


# ============================================
# PUROK MODEL TESTS
# ============================================

class TestPurokModel:
    """Test Purok operations."""
    
    def test_get_all_puroks(self, setup_database):
        """Test retrieving all puroks (seeded data)."""
        puroks = PurokModel.get_all()
        
        assert isinstance(puroks, list)
        assert len(puroks) > 0  # Default seed data exists
    
    def test_create_purok(self, setup_database):
        """Test creating a new purok."""
        purok_id = PurokModel.create(
            purok_name="Test Purok",
            assigned_tanod_leader="Juan Test"
        )
        
        assert purok_id is not None
        
        purok = PurokModel.get_by_id(purok_id)
        assert purok["purok_name"] == "Test Purok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
