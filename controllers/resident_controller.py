"""
KALASAG - Resident Controller
Handles business logic between Resident Views and Models.
"""

from models.resident import ResidentModel, HouseholdModel, PurokModel
from utils.validators import (
    validate_required, validate_name, validate_birthdate,
    validate_sex, validate_civil_status, validate_contact_number,
    sanitize_input
)
from typing import Dict, Any, List, Tuple, Optional


class ResidentController:
    """Controller for Resident operations."""
    
    def __init__(self, current_user_id: int = None):
        """
        Initialize the controller.
        
        Args:
            current_user_id: ID of the currently logged-in user (for audit)
        """
        self.current_user_id = current_user_id
    
    def validate_resident_data(self, data: Dict[str, Any], 
                                is_update: bool = False) -> Tuple[bool, List[str]]:
        """
        Validate resident form data.
        
        Args:
            data: Dictionary of resident fields
            is_update: If True, required fields may be optional
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Required fields (only for create)
        if not is_update:
            valid, error = validate_required(data.get('first_name', ''), 'First Name')
            if not valid:
                errors.append(error)
            
            valid, error = validate_required(data.get('last_name', ''), 'Last Name')
            if not valid:
                errors.append(error)
        
        # Validate name fields if provided
        if data.get('first_name'):
            valid, error = validate_name(data['first_name'], 'First Name')
            if not valid:
                errors.append(error)
        
        if data.get('middle_name'):
            valid, error = validate_name(data['middle_name'], 'Middle Name')
            if not valid:
                errors.append(error)
        
        if data.get('last_name'):
            valid, error = validate_name(data['last_name'], 'Last Name')
            if not valid:
                errors.append(error)
        
        # Validate other fields
        if data.get('birthdate'):
            valid, error = validate_birthdate(data['birthdate'])
            if not valid:
                errors.append(error)
        
        if data.get('sex'):
            valid, error = validate_sex(data['sex'])
            if not valid:
                errors.append(error)
        
        if data.get('civil_status'):
            valid, error = validate_civil_status(data['civil_status'])
            if not valid:
                errors.append(error)
        
        if data.get('contact_number'):
            valid, error = validate_contact_number(data['contact_number'])
            if not valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    def create_resident(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Create a new resident.
        
        Args:
            data: Resident data dictionary
            
        Returns:
            Tuple of (success, resident_id or error message)
        """
        # Validate
        is_valid, errors = self.validate_resident_data(data)
        if not is_valid:
            return False, errors
        
        # Sanitize inputs
        sanitized = {k: sanitize_input(v) if isinstance(v, str) else v 
                    for k, v in data.items()}
        
        try:
            res_id = ResidentModel.create(
                first_name=sanitized.get('first_name'),
                last_name=sanitized.get('last_name'),
                middle_name=sanitized.get('middle_name'),
                alias=sanitized.get('alias'),
                birthdate=sanitized.get('birthdate'),
                sex=sanitized.get('sex'),
                civil_status=sanitized.get('civil_status'),
                occupation=sanitized.get('occupation'),
                purok_id=sanitized.get('purok_id'),
                hh_id=sanitized.get('hh_id'),
                is_indigent=sanitized.get('is_indigent', False),
                status=sanitized.get('status', 'Active'),
                photo_blob=sanitized.get('photo_blob'),
                contact_number=sanitized.get('contact_number'),
                user_id=self.current_user_id
            )
            return True, res_id
        except Exception as e:
            return False, [str(e)]
    
    def update_resident(self, res_id: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Update an existing resident.
        
        Args:
            res_id: Resident ID to update
            data: Fields to update
            
        Returns:
            Tuple of (success, True or error messages)
        """
        # Validate
        is_valid, errors = self.validate_resident_data(data, is_update=True)
        if not is_valid:
            return False, errors
        
        # Sanitize inputs
        sanitized = {k: sanitize_input(v) if isinstance(v, str) else v 
                    for k, v in data.items()}
        
        try:
            success = ResidentModel.update(
                res_id=res_id,
                user_id=self.current_user_id,
                **sanitized
            )
            if success:
                return True, True
            else:
                return False, ["No changes made or resident not found"]
        except Exception as e:
            return False, [str(e)]
    
    def get_resident(self, res_id: int) -> Optional[Dict[str, Any]]:
        """Get a resident by ID."""
        return ResidentModel.get_by_id(res_id)
    
    def get_all_residents(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get all residents with optional filters.
        
        Args:
            filters: Optional dict with 'status', 'purok_id', 'is_indigent'
        """
        filters = filters or {}
        return ResidentModel.get_all(
            status=filters.get('status'),
            purok_id=filters.get('purok_id'),
            is_indigent=filters.get('is_indigent')
        )
    
    def search_residents(self, keyword: str, search_by: str = "all") -> List[Dict[str, Any]]:
        """
        Search residents (FR-1.3).
        
        Args:
            keyword: Search term
            search_by: 'name', 'alias', 'household', or 'all'
        """
        if not keyword or not keyword.strip():
            return []
        
        return ResidentModel.search(keyword.strip(), search_by)
    
    def update_resident_status(self, res_id: int, status: str) -> Tuple[bool, Any]:
        """Update resident status (FR-1.4)."""
        try:
            success = ResidentModel.update_status(res_id, status, self.current_user_id)
            return success, True if success else "Failed to update status"
        except ValueError as e:
            return False, [str(e)]
    
    def update_indigent_status(self, res_id: int, is_indigent: bool) -> Tuple[bool, Any]:
        """Update resident indigent status (FR-1.4)."""
        try:
            success = ResidentModel.update_indigent_status(
                res_id, is_indigent, self.current_user_id
            )
            return success, True if success else "Failed to update indigent status"
        except Exception as e:
            return False, [str(e)]
    
    def delete_resident(self, res_id: int) -> Tuple[bool, Any]:
        """Delete a resident."""
        try:
            success = ResidentModel.delete(res_id, self.current_user_id)
            return success, True if success else "Resident not found"
        except ValueError as e:
            return False, [str(e)]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get resident statistics for dashboard."""
        return ResidentModel.get_statistics()
    
    def get_puroks(self) -> List[Dict[str, Any]]:
        """Get all puroks for dropdown."""
        return PurokModel.get_all()
    
    def get_all_puroks(self) -> List[Dict[str, Any]]:
        """Get all puroks (alias for get_puroks)."""
        return PurokModel.get_all()
    
    def get_all_households(self) -> List[Dict[str, Any]]:
        """Get all households."""
        return HouseholdModel.get_all()
    
    def create_household(self, house_number: str, street_name: str, 
                         purok_id: int = None) -> Tuple[bool, Any]:
        """Create a new household."""
        if not house_number or not house_number.strip():
            return False, "House number is required"
        if not street_name or not street_name.strip():
            return False, "Street name is required"
        
        try:
            hh_id = HouseholdModel.create(
                house_number=sanitize_input(house_number),
                street_name=sanitize_input(street_name),
                purok_id=purok_id
            )
            return True, hh_id
        except Exception as e:
            return False, str(e)
    
    def add_household(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """Add a new household (convenience method)."""
        # Handle 'address' field - split into house_number and street_name
        address = data.get('address', '')
        parts = address.split(' ', 1) if address else ['', '']
        house_number = parts[0] if parts else ''
        street_name = parts[1] if len(parts) > 1 else address
        
        return self.create_household(
            house_number=data.get('house_number', house_number),
            street_name=data.get('street_name', street_name),
            purok_id=data.get('purok_id')
        )
    
    def add_purok(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """Add a new purok."""
        return self.create_purok(data.get('purok_name'), data.get('assigned_tanod_leader'))
    
    def create_purok(self, purok_name: str, assigned_tanod_leader: str = None) -> Tuple[bool, Any]:
        """Create a new purok."""
        if not purok_name or not purok_name.strip():
            return False, "Purok name is required"
        try:
            purok_id = PurokModel.create(
                purok_name=sanitize_input(purok_name),
                assigned_tanod_leader=sanitize_input(assigned_tanod_leader) if assigned_tanod_leader else None
            )
            return True, purok_id
        except Exception as e:
            return False, str(e)
    
    def update_purok(self, purok_id: int, purok_name: str = None, 
                     assigned_tanod_leader: str = None) -> Tuple[bool, Any]:
        """Update a purok."""
        try:
            success = PurokModel.update(
                purok_id=purok_id,
                purok_name=sanitize_input(purok_name) if purok_name else None,
                assigned_tanod_leader=sanitize_input(assigned_tanod_leader) if assigned_tanod_leader else None
            )
            return success, True if success else "No changes made"
        except Exception as e:
            return False, str(e)
    
    def delete_purok(self, purok_id: int) -> Tuple[bool, Any]:
        """Delete a purok."""
        try:
            success = PurokModel.delete(purok_id)
            return success, True if success else "Purok not found"
        except ValueError as e:
            return False, str(e)
    
    def update_household(self, hh_id: int, house_number: str = None,
                         street_name: str = None, purok_id: int = None) -> Tuple[bool, Any]:
        """Update a household."""
        try:
            success = HouseholdModel.update(
                hh_id=hh_id,
                house_number=sanitize_input(house_number) if house_number else None,
                street_name=sanitize_input(street_name) if street_name else None,
                purok_id=purok_id
            )
            return success, True if success else "No changes made"
        except Exception as e:
            return False, str(e)


class HouseholdController:
    """Controller for Household operations."""
    
    def __init__(self, current_user_id: int = None):
        self.current_user_id = current_user_id
    
    def create_household(self, house_number: str, street_name: str, 
                         purok_id: int = None) -> Tuple[bool, Any]:
        """Create a new household."""
        if not house_number or not house_number.strip():
            return False, ["House number is required"]
        if not street_name or not street_name.strip():
            return False, ["Street name is required"]
        
        try:
            hh_id = HouseholdModel.create(
                house_number=sanitize_input(house_number),
                street_name=sanitize_input(street_name),
                purok_id=purok_id
            )
            return True, hh_id
        except Exception as e:
            return False, [str(e)]
    
    def get_household(self, hh_id: int) -> Optional[Dict[str, Any]]:
        """Get a household by ID."""
        return HouseholdModel.get_by_id(hh_id)
    
    def get_all_households(self) -> List[Dict[str, Any]]:
        """Get all households."""
        return HouseholdModel.get_all()
    
    def get_household_members(self, hh_id: int) -> List[Dict[str, Any]]:
        """Get all members of a household (FR-1.2)."""
        return HouseholdModel.get_members(hh_id)
    
    def update_household(self, hh_id: int, house_number: str = None,
                         street_name: str = None, purok_id: int = None) -> Tuple[bool, Any]:
        """Update a household."""
        try:
            success = HouseholdModel.update(
                hh_id=hh_id,
                house_number=sanitize_input(house_number) if house_number else None,
                street_name=sanitize_input(street_name) if street_name else None,
                purok_id=purok_id
            )
            return success, True if success else "No changes made"
        except Exception as e:
            return False, [str(e)]
    
    def delete_household(self, hh_id: int) -> Tuple[bool, Any]:
        """Delete a household."""
        try:
            success = HouseholdModel.delete(hh_id)
            return success, True if success else "Household not found"
        except ValueError as e:
            return False, [str(e)]
