"""
KALASAG - Blotter Controller
Handles business logic for E-Blotter & Case Management.
Implements FR-2.1, FR-2.2, FR-2.3, FR-2.4
"""

from models.blotter import BlotterCaseModel, CaseInvolvementModel, IncidentTypeModel
from models.resident import ResidentModel, PurokModel
from utils.validators import validate_required, validate_narrative, sanitize_input
from utils.helpers import format_name
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class BlotterController:
    """Controller for Blotter Case operations."""
    
    def __init__(self, current_user_id: int = None):
        """
        Initialize the controller.
        
        Args:
            current_user_id: ID of the currently logged-in user (for audit)
        """
        self.current_user_id = current_user_id
    
    def validate_blotter_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate blotter case form data.
        
        Args:
            data: Dictionary of blotter case fields
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Required: date_time
        if not data.get('date_time'):
            errors.append("Incident date/time is required")
        else:
            # Validate date format
            try:
                dt = datetime.fromisoformat(data['date_time'].replace('Z', '+00:00'))
                if dt > datetime.now():
                    errors.append("Incident date/time cannot be in the future")
            except ValueError:
                errors.append("Invalid date/time format")
        
        # Required: narrative (min 10 characters)
        valid, error = validate_narrative(data.get('narrative', ''))
        if not valid:
            errors.append(error)
        
        # At least one complainant or respondent should be specified
        if not data.get('complainants') and not data.get('respondents'):
            errors.append("At least one complainant or respondent is required")
        
        return len(errors) == 0, errors
    
    def check_respondent_recidivism(self, respondent_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Check all respondents for prior cases (FR-2.4).
        
        Args:
            respondent_ids: List of resident IDs to check
            
        Returns:
            List of recidivist alerts with resident info and prior cases
        """
        alerts = []
        
        for res_id in respondent_ids:
            result = CaseInvolvementModel.check_recidivist(res_id)
            
            if result['is_recidivist']:
                # Get resident name
                resident = ResidentModel.get_by_id(res_id)
                if resident:
                    name = format_name(
                        resident['first_name'],
                        resident.get('middle_name'),
                        resident['last_name']
                    )
                    alerts.append({
                        'res_id': res_id,
                        'name': name,
                        'alias': resident.get('alias'),
                        'prior_cases': result['prior_cases'],
                        'case_numbers': result['case_numbers'],
                        'message': f"⚠️ {name} has {result['prior_cases']} prior blotter record(s)"
                    })
        
        return alerts
    
    def create_blotter_case(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Create a new blotter case (FR-2.1, FR-2.2).
        
        Args:
            data: Blotter case data dictionary containing:
                - date_time: Incident date/time
                - narrative: Incident description
                - purok_id: Location (optional)
                - type_id: Incident type (optional)
                - complainants: List of resident IDs
                - respondents: List of resident IDs
                - witnesses: List of resident IDs (optional)
            
        Returns:
            Tuple of (success, (case_id, case_number, recidivist_alerts) or error messages)
        """
        # Validate
        is_valid, errors = self.validate_blotter_data(data)
        if not is_valid:
            return False, errors
        
        # Check for recidivists before creating (FR-2.4)
        recidivist_alerts = []
        if data.get('respondents'):
            recidivist_alerts = self.check_respondent_recidivism(data['respondents'])
        
        # Sanitize narrative
        narrative = sanitize_input(data.get('narrative', ''))
        
        try:
            case_id, case_number = BlotterCaseModel.create(
                date_time=data['date_time'],
                narrative=narrative,
                purok_id=data.get('purok_id'),
                type_id=data.get('type_id'),
                recorded_by=self.current_user_id,
                complainants=data.get('complainants', []),
                respondents=data.get('respondents', []),
                witnesses=data.get('witnesses', [])
            )
            
            return True, {
                'case_id': case_id,
                'case_number': case_number,
                'recidivist_alerts': recidivist_alerts
            }
            
        except Exception as e:
            return False, [str(e)]
    
    def get_blotter_case(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Get a blotter case by ID with all related data."""
        return BlotterCaseModel.get_by_id(case_id)
    
    def get_case(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Alias for get_blotter_case."""
        return self.get_blotter_case(case_id)
    
    def get_case_involvements(self, case_id: int) -> List[Dict[str, Any]]:
        """Get all persons involved in a case."""
        return CaseInvolvementModel.get_involvements(case_id)

    def get_blotter_by_case_number(self, case_number: str) -> Optional[Dict[str, Any]]:
        """Get a blotter case by case number."""
        return BlotterCaseModel.get_by_case_number(case_number)
    
    def get_all_cases(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get all blotter cases with optional filters.
        
        Args:
            filters: Optional dict with 'status', 'purok_id', 'type_id', 
                    'start_date', 'end_date', 'limit'
        """
        filters = filters or {}
        return BlotterCaseModel.get_all(
            status=filters.get('status'),
            purok_id=filters.get('purok_id'),
            type_id=filters.get('type_id'),
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date'),
            limit=filters.get('limit')
        )
    
    def search_cases(self, keyword: str) -> List[Dict[str, Any]]:
        """Search blotter cases by case number or narrative."""
        if not keyword or not keyword.strip():
            return []
        return BlotterCaseModel.search(keyword.strip())
    
    def update_case_status(self, case_id: int, status: str) -> Tuple[bool, Any]:
        """
        Update blotter case status (FR-2.3).
        
        Args:
            case_id: Case ID to update
            status: New status
        """
        try:
            success = BlotterCaseModel.update_status(
                case_id, status, self.current_user_id
            )
            return success, True if success else "Failed to update status"
        except ValueError as e:
            return False, [str(e)]
    
    def update_blotter_case(self, case_id: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Update blotter case details.
        
        Args:
            case_id: Case ID to update
            data: Fields to update
        """
        try:
            # Validate narrative if provided
            if 'narrative' in data:
                valid, error = validate_narrative(data['narrative'])
                if not valid:
                    return False, [error]
                data['narrative'] = sanitize_input(data['narrative'])
            
            success = BlotterCaseModel.update(
                case_id, 
                user_id=self.current_user_id,
                **data
            )
            return success, True if success else "No changes made"
        except Exception as e:
            return False, [str(e)]
    
    def delete_blotter_case(self, case_id: int) -> Tuple[bool, Any]:
        """Delete a blotter case."""
        try:
            success = BlotterCaseModel.delete(case_id, self.current_user_id)
            return success, True if success else "Case not found"
        except Exception as e:
            return False, [str(e)]
    
    def add_person_to_case(self, case_id: int, res_id: int, role: str) -> Tuple[bool, Any]:
        """
        Add a person to a case (FR-2.2).
        
        Also checks for recidivism if adding as Respondent (FR-2.4).
        """
        recidivist_alert = None
        
        # Check recidivism if adding as respondent
        if role == 'Respondent':
            alerts = self.check_respondent_recidivism([res_id])
            if alerts:
                recidivist_alert = alerts[0]
        
        try:
            link_id = CaseInvolvementModel.add_involvement(case_id, res_id, role)
            return True, {
                'link_id': link_id,
                'recidivist_alert': recidivist_alert
            }
        except ValueError as e:
            return False, [str(e)]
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                return False, ["This person is already added with this role"]
            return False, [str(e)]
    
    def remove_person_from_case(self, case_id: int, res_id: int, 
                                 role: str = None) -> Tuple[bool, Any]:
        """Remove a person from a case."""
        try:
            success = CaseInvolvementModel.remove_involvement(case_id, res_id, role)
            return success, True if success else "Person not found in case"
        except Exception as e:
            return False, [str(e)]
    
    def get_resident_cases(self, res_id: int, role: str = None) -> List[Dict[str, Any]]:
        """Get all cases involving a specific resident."""
        return BlotterCaseModel.get_cases_by_resident(res_id, role)
    
    def get_statistics(self, start_date: str = None, 
                       end_date: str = None) -> Dict[str, Any]:
        """Get blotter statistics for dashboard."""
        return BlotterCaseModel.get_statistics(start_date, end_date)
    
    def get_incident_types(self) -> List[Dict[str, Any]]:
        """Get all incident types for dropdown."""
        return IncidentTypeModel.get_all()
    
    def get_puroks(self) -> List[Dict[str, Any]]:
        """Get all puroks for location dropdown."""
        return PurokModel.get_all()
    
    def get_pending_cases(self) -> List[Dict[str, Any]]:
        """Get all pending cases."""
        return BlotterCaseModel.get_all(status='Pending')
    
    def create_case(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """Convenience method for creating a blotter case from the form."""
        # Map form data to controller data format
        case_data = {
            'date_time': data.get('date_time'),
            'narrative': data.get('narrative'),
            'type_id': data.get('type_id'),
            'purok_id': data.get('purok_id'),
            'complainants': data.get('complainants', []),
            'respondents': data.get('respondents', []),
            'witnesses': data.get('witnesses', [])
        }
        
        # Set the current user for recording
        self.current_user_id = data.get('reported_by')
        
        return self.create_blotter_case(case_data)
    
    def update_case(self, case_id: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """Convenience method for updating a blotter case from the form."""
        # Handle status update separately if present
        if 'status' in data:
            return self.update_case_status(case_id, data['status'])
            
        return self.update_blotter_case(case_id, data)
    
    def get_recent_cases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent cases."""
        return BlotterCaseModel.get_all(limit=limit)


class IncidentTypeController:
    """Controller for Incident Type operations."""
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all incident types."""
        return IncidentTypeModel.get_all()
    
    @staticmethod
    def get_by_id(type_id: int) -> Optional[Dict[str, Any]]:
        """Get an incident type by ID."""
        return IncidentTypeModel.get_by_id(type_id)
    
    @staticmethod
    def create(name: str, severity: int, description: str = None) -> Tuple[bool, Any]:
        """Create a new incident type."""
        if not name or not name.strip():
            return False, ["Name is required"]
        
        if severity < 1 or severity > 5:
            return False, ["Severity must be between 1 and 5"]
        
        try:
            type_id = IncidentTypeModel.create(
                name=sanitize_input(name),
                severity=severity,
                description=sanitize_input(description) if description else None
            )
            return True, type_id
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                return False, ["An incident type with this name already exists"]
            return False, [str(e)]
    
    @staticmethod
    def update(type_id: int, name: str = None, severity: int = None,
               description: str = None) -> Tuple[bool, Any]:
        """Update an incident type."""
        try:
            success = IncidentTypeModel.update(
                type_id,
                name=sanitize_input(name) if name else None,
                severity=severity,
                description=sanitize_input(description) if description else None
            )
            return success, True if success else "No changes made"
        except ValueError as e:
            return False, [str(e)]
