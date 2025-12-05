# 🛡️ KALASAG - Requirements Traceability Matrix (RTM)

**Document Version:** 1.0  
**Date:** December 5, 2025  
**Project:** Barangay Information System with Predictive Crime Analytics  
**Status:** Development Phase - Integration Testing

---

## 📋 Overview

This Requirements Traceability Matrix (RTM) maps each functional requirement from `requirements.md` to its corresponding implementation artifacts (models, controllers, views) and test cases.

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully Implemented |
| 🔧 | Implemented with Known Issues |
| 🚧 | Partially Implemented |
| ❌ | Not Yet Implemented |

---

## 🏠 Module 1: Resident Information System (RIS)

| Req ID | Requirement Description | Status | Implementation | Test Coverage |
|--------|------------------------|--------|----------------|---------------|
| **FR-1.1** | Create resident profiles: Name, Birthdate, Sex, Civil Status, Address (Purok), Occupation, Photo | ✅ | `models/resident.py` → `ResidentModel.create()`<br>`controllers/resident_controller.py` → `ResidentController.create_resident()`<br>`views/resident_view.py` → `ResidentFormDialog` | `tests/test_resident.py` → `TestResidentModel`, `TestResidentController` |
| **FR-1.2** | Group residents under unique Household ID | ✅ | `models/resident.py` → `HouseholdModel`<br>`database.py` → `household` table with `hh_id`<br>`views/resident_view.py` → `HouseholdFormDialog` | `tests/test_resident.py` → `TestHouseholdModel` |
| **FR-1.3** | Search capability by Name, Alias, or Household ID | ✅ | `models/resident.py` → `ResidentModel.search()`<br>`controllers/resident_controller.py` → `ResidentController.search_residents()`<br>`views/resident_view.py` → Search bar in `ResidentView` | `tests/test_resident.py` → `test_search_residents()` |
| **FR-1.4** | Tag residents as Active, Deceased, Moved Out, or Indigent | ✅ | `database.py` → `resident.status` CHECK constraint<br>`database.py` → `resident.is_indigent` boolean<br>`models/resident.py` → `ResidentModel.update()` | `tests/test_resident.py` → Status validation tests |

### RIS Data Schema

| Table | Primary Key | Key Fields | Foreign Keys |
|-------|-------------|------------|--------------|
| `resident` | `res_id` | first_name, last_name, sex, birthdate, status, is_indigent | `hh_id` → household, `purok_id` → purok |
| `household` | `hh_id` | house_number, street_name | `purok_id` → purok |
| `purok` | `purok_id` | purok_name, assigned_tanod_leader | None |

---

## 📝 Module 2: E-Blotter & Case Management

| Req ID | Requirement Description | Status | Implementation | Test Coverage |
|--------|------------------------|--------|----------------|---------------|
| **FR-2.1** | Record incident details: Date/Time, Narrative, Incident Type, Location (Purok) | ✅ | `models/blotter.py` → `BlotterCaseModel.create()`<br>`controllers/blotter_controller.py` → `BlotterController.create_blotter_case()`<br>`views/blotter_view.py` → `CaseFormDialog` | `tests/test_blotter.py` → `TestBlotterCaseModel.test_create_blotter_case()` |
| **FR-2.2** | Link existing Resident Profiles as Complainant or Respondent | ✅ | `models/blotter.py` → `CaseInvolvementModel`<br>`database.py` → `case_involvement` table with role field<br>`controllers/blotter_controller.py` → `add_person_to_case()` | `tests/test_blotter.py` → `TestCaseInvolvementModel` |
| **FR-2.3** | Track case status: Pending, Amicable Settlement, Escalated to PNP, Closed | ✅ | `database.py` → `blotter_case.status` CHECK constraint<br>`models/blotter.py` → `BlotterCaseModel.update_status()`<br>`controllers/blotter_controller.py` → `update_case_status()` | `tests/test_blotter.py` → `test_update_status_via_controller()` |
| **FR-2.4** | Recidivist Alert: Warn if Respondent has prior blotter cases | ✅ | `database.py` → `check_recidivist()`<br>`controllers/blotter_controller.py` → `check_respondent_recidivism()`<br>Auto-triggered in `create_blotter_case()` | `tests/test_blotter.py` → `test_recidivist_alert_on_create()` |

### Blotter Data Schema

| Table | Primary Key | Key Fields | Foreign Keys |
|-------|-------------|------------|--------------|
| `blotter_case` | `case_id` | case_number, date_time, narrative, status | `purok_id` → purok, `type_id` → incident_type, `recorded_by` → user |
| `case_involvement` | `link_id` | role (Complainant/Respondent/Witness) | `case_id` → blotter_case, `res_id` → resident |
| `incident_type` | `type_id` | name, severity (1-5) | None |

---

## 📄 Module 3: Document Issuance

| Req ID | Requirement Description | Status | Implementation | Test Coverage |
|--------|------------------------|--------|----------------|---------------|
| **FR-3.1** | Auto-generate PDF documents (Clearance, Indigency, Permit) using stored resident data | ✅ | `utils/pdf_generator.py` → `PDFGenerator` class<br>`controllers/document_controller.py` → `issue_document()`<br>`views/document_view.py` → `DocumentView` | `tests/test_document.py` → `TestPDFGenerator` |
| **FR-3.2** | Auto-assign unique, non-editable Control Numbers to prevent fraud | ✅ | `database.py` → `generate_control_number()`<br>`models/document.py` → `DocumentModel.create()` auto-generates control_number | `tests/test_document.py` → `test_control_number_uniqueness()` |
| **FR-3.3** | Log Official Receipt (O.R.) Number and Amount Paid | ✅ | `database.py` → `doc_log` table with `or_number`, `amount` fields<br>`models/document.py` → `DocumentModel.update_payment()`<br>`controllers/document_controller.py` → `update_payment()` | `tests/test_document.py` → `test_update_payment()` |

### Document Data Schema

| Table | Primary Key | Key Fields | Foreign Keys |
|-------|-------------|------------|--------------|
| `doc_log` | `doc_id` | control_number, doc_type, amount, or_number, purpose | `res_id` → resident, `issued_by` → user |

### Supported Document Types

| Document Type | Code | Default Fee | PDF Template |
|--------------|------|-------------|--------------|
| Barangay Clearance | `clearance` | ₱50.00 | ✅ Implemented |
| Certificate of Indigency | `indigency` | ₱0.00 | ✅ Implemented |
| Business Permit | `permit` | ₱100.00 | ✅ Implemented |
| Certificate of Residency | `residency` | ₱50.00 | ✅ Implemented |

---

## 📊 Module 4: Intelligence & Analytics (BI Core)

| Req ID | Requirement Description | Status | Implementation | Test Coverage |
|--------|------------------------|--------|----------------|---------------|
| **FR-4.1** | Crime Heatmap: Color-coded visualization (Green/Yellow/Red) per Purok | ✅ | `models/analytics.py` → `AnalyticsModel.get_purok_crime_density()`<br>`controllers/analytics_controller.py` → `get_crime_heatmap()`<br>`views/analytics_view.py` → Matplotlib charts | `tests/test_analytics.py` → `TestCrimeHeatmap` |
| **FR-4.2** | Time-Series Analysis: Chart showing "Most Dangerous Time of Day" | ✅ | `models/analytics.py` → `AnalyticsModel.get_time_analysis()`<br>`controllers/analytics_controller.py` → `get_time_series_analysis()`<br>`views/analytics_view.py` → Time distribution chart | `tests/test_analytics.py` → `TestTimeAnalysis` |
| **FR-4.3** | Patrol Recommender: Text output suggesting deployment locations/times | ✅ | `models/analytics.py` → `AnalyticsModel.get_patrol_recommendations()`<br>`controllers/analytics_controller.py` → `get_patrol_recommendations()`<br>`views/analytics_view.py` → Recommendations panel | `tests/test_analytics.py` → `TestPatrolRecommendations` |

### Hotspot Logic Implementation (Section 6.1)

```
Rule Applied in: models/analytics.py → get_purok_crime_density()

Count = 0:     🟢 Green (Safe)
Count 1-3:    🟡 Yellow (Caution)  
Count > 3:    🔴 Red (Hotspot)

Time Window: Last 30 days (configurable)
```

### Recidivism Logic Implementation (Section 6.2)

```
Trigger: User selects Resident for "Respondent" field
Check:   database.py → check_recidivist(res_id)
Alert:   "⚠️ Subject has prior blotter records."
```

---

## ⚙️ Module 5: System Administration

| Req ID | Requirement Description | Status | Implementation | Test Coverage |
|--------|------------------------|--------|----------------|---------------|
| **FR-5.1** | One-Click Database Backup (.SQL/.CSV export) | ✅ | `models/admin.py` → `BackupModel`<br>`controllers/admin_controller.py` → `create_backup()`, `export_to_csv()`<br>`views/admin_view.py` → Backup/Export buttons | `tests/test_admin.py` → `TestBackupRestore` |
| **FR-5.2** | Audit Trail logging sensitive actions | ✅ | `database.py` → `log_audit()`, `audit_log` table<br>`models/admin.py` → `AuditLogModel`<br>`controllers/admin_controller.py` → `get_audit_logs()` | `tests/test_admin.py` → `TestAuditLogModel` |

### Admin Data Schema

| Table | Primary Key | Key Fields | Foreign Keys |
|-------|-------------|------------|--------------|
| `user` | `user_id` | username, password_hash, full_name, role, is_active | `created_by` → user |
| `audit_log` | `log_id` | action, table_name, record_id, old_values, new_values, timestamp | `user_id` → user |
| `settings` | `setting_id` | setting_key, setting_value | `updated_by` → user |
| `backup` | `backup_id` | filename, filepath, file_size, backup_type | `created_by` → user |

---

## 🧱 Non-Functional Requirements (NFR)

| NFR ID | Requirement | Status | Implementation |
|--------|-------------|--------|----------------|
| **NFR-1** | UI/UX: Unified color palette, consistent fonts, standardized widgets | ✅ | `views/theme.py` → `KalasagTheme` class<br>Corporate Blue/Slate Gray palette<br>ttk themed widgets |
| **NFR-2** | Visual Hierarchy: Proper font weights, whitespace, information architecture | ✅ | `views/theme.py` → Font constants (`FONT_HEADER`, `FONT_BODY`)<br>Padding constants (`PAD_SMALL`, `PAD_MEDIUM`, `PAD_LARGE`) |
| **NFR-3** | Feedback & Affordance: Cursor changes, active states, progress indicators | 🔧 | Basic implementation in widgets<br>Status bar messages via `status_callback` |
| **NFR-4** | Performance: Search < 2 seconds for 10,000 records | 🚧 | SQL indexes created in `database.py`<br>Not yet load-tested |
| **NFR-5** | Reliability: 100% Offline operation | ✅ | SQLite local database<br>No external API dependencies |
| **NFR-6** | Security: SHA-256 password hashing | ✅ | `database.py` → `hash_password()` using hashlib |
| **NFR-7** | Security: SQL Injection prevention | ✅ | Parameterized queries throughout models |
| **NFR-8** | Deployment: Windows 10/11 compatible | ✅ | Standard Python + Tkinter<br>No complex external dependencies |

---

## 🗄️ Database Schema Verification

| Schema Element | Defined In | Implementation Status |
|----------------|------------|----------------------|
| Residents table | Section 5.I | ✅ `database.py` line 70-90 |
| Households table | Section 5.I | ✅ `database.py` line 53-61 |
| Puroks table | Section 5.I | ✅ `database.py` line 44-51 |
| IncidentTypes table | Section 5.II | ✅ `database.py` line 100-108 |
| BlotterCases table | Section 5.II | ✅ `database.py` line 114-129 |
| CaseInvolvement table | Section 5.II | ✅ `database.py` line 133-143 |
| DocLogs table | Section 5.III | ✅ `database.py` line 147-162 |
| AuditLogs table | Section 5.III | ✅ `database.py` line 166-178 |

---

## 🧪 Test Coverage Summary

| Module | Test File | Test Classes | Key Test Cases |
|--------|-----------|--------------|----------------|
| **RIS (FR-1.x)** | `tests/test_resident.py` | `TestResidentModel`, `TestHouseholdModel`, `TestResidentController` | CRUD operations, search, validation |
| **Blotter (FR-2.x)** | `tests/test_blotter.py` | `TestBlotterCaseModel`, `TestCaseInvolvementModel`, `TestBlotterController` | Case creation, status updates, recidivist alerts |
| **Documents (FR-3.x)** | `tests/test_document.py` | `TestDocumentModel`, `TestDocumentController`, `TestPDFGenerator` | Document issuance, control numbers, payments |
| **Analytics (FR-4.x)** | `tests/test_analytics.py` | `TestCrimeHeatmap`, `TestTimeAnalysis`, `TestPatrolRecommendations` | Heatmap logic, time analysis, recommendations |
| **Admin (FR-5.x)** | `tests/test_admin.py` | `TestAuditLogModel`, `TestBackupRestore`, `TestUserManagement` | Audit trails, backup/restore, user CRUD |

---

## 📂 File Traceability Matrix

### Models Layer (`models/`)

| File | Implements | Classes |
|------|------------|---------|
| `resident.py` | FR-1.1, FR-1.2, FR-1.3, FR-1.4 | `ResidentModel`, `HouseholdModel`, `PurokModel` |
| `blotter.py` | FR-2.1, FR-2.2, FR-2.3, FR-2.4 | `BlotterCaseModel`, `CaseInvolvementModel`, `IncidentTypeModel` |
| `document.py` | FR-3.1, FR-3.2, FR-3.3 | `DocumentModel` |
| `analytics.py` | FR-4.1, FR-4.2, FR-4.3 | `AnalyticsModel` |
| `admin.py` | FR-5.1, FR-5.2 | `AuditLogModel`, `BackupModel`, `SystemSettingsModel` |
| `user.py` | User Authentication | `UserModel` |

### Controllers Layer (`controllers/`)

| File | Implements | Classes |
|------|------------|---------|
| `resident_controller.py` | FR-1.x business logic | `ResidentController`, `HouseholdController` |
| `blotter_controller.py` | FR-2.x business logic | `BlotterController`, `IncidentTypeController` |
| `document_controller.py` | FR-3.x business logic | `DocumentController` |
| `analytics_controller.py` | FR-4.x business logic | `AnalyticsController` |
| `admin_controller.py` | FR-5.x business logic | `AdminController` |

### Views Layer (`views/`)

| File | Implements | Classes |
|------|------------|---------|
| `resident_view.py` | FR-1.x UI | `ResidentView`, `ResidentFormDialog`, `HouseholdFormDialog`, `PurokFormDialog` |
| `blotter_view.py` | FR-2.x UI | `BlotterView`, `CaseFormDialog`, `CaseDetailDialog` |
| `document_view.py` | FR-3.x UI | `DocumentView`, `IssueDocumentDialog` |
| `analytics_view.py` | FR-4.x UI | `AnalyticsView` (charts, recommendations) |
| `admin_view.py` | FR-5.x UI | `AdminView`, `UserFormDialog`, `BackupDialog` |
| `dashboard_view.py` | System Overview | `DashboardView` |
| `login_view.py` | Authentication | `LoginView` |
| `main_app.py` | Main Window | `MainApp` |
| `theme.py` | NFR-1, NFR-2 | `KalasagTheme` |
| `components.py` | Reusable Widgets | `DataTable`, `SearchFrame`, `CardWidget`, `StatusBadge` |

### Utilities Layer (`utils/`)

| File | Implements | Functions/Classes |
|------|------------|-------------------|
| `validators.py` | Input validation | `validate_name()`, `validate_birthdate()`, `sanitize_input()` |
| `helpers.py` | Utility functions | `format_name()`, `format_date()`, `calculate_age()` |
| `pdf_generator.py` | FR-3.1 PDF generation | `PDFGenerator` class |

---

## 🔄 Sign-off Criteria Status

| Criteria | Status | Evidence |
|----------|--------|----------|
| 1. All Unit Tests pass | 🔧 | Tests exist, some debugging in progress |
| 2. Add Resident and print Clearance PDF | ✅ | `ResidentView` + `DocumentView` + `PDFGenerator` |
| 3. Log Blotter Incident linked to Resident | ✅ | `BlotterView` + `CaseInvolvementModel` |
| 4. Dashboard Graph updates on new Blotter | ✅ | `DashboardView` calls `AnalyticsController` |
| 5. Generate Monthly Peace & Order Report | 🚧 | PDF report generation partially implemented |

---

## 📝 Known Issues & Debugging Notes

| Issue ID | Module | Description | Status |
|----------|--------|-------------|--------|
| BUG-001 | Admin | `create_user()` argument mismatch | Fixed |
| BUG-002 | Resident | Field mapping (sex vs gender, hh_id) | Fixed |
| BUG-003 | Blotter | `create_case()` method naming | Fixed |
| BUG-004 | Dashboard | Navigation callback missing | Fixed |
| BUG-005 | Analytics | SQL column name mismatches | Fixed |

---

## 📅 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-05 | Initial RTM creation |

---

*Generated for KALASAG - Barangay Information System Project*
