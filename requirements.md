# 🛡️ Project: KALASAG
### Barangay Information System (BIS) with Predictive Crime Analytics

**Document Version:** 1.3  
**Date:** October 24, 2023  
**Status:** Requirements Analysis Phase

---

## 📋 1. Introduction

### 1.1 Purpose
The purpose of this document is to define the operational, functional, and data requirements for **KALASAG** (Tagalog for *Shield*). This desktop application aims to modernize Barangay Local Government Unit (BLGU) operations by transitioning from manual logbooks to a centralized SQL database. It specifically targets the enhancement of peace and order via **Business Intelligence (BI)**, analyzing blotter data to predict crime hotspots and optimize Tanod (patrol) deployment.

### 1.2 Scope
The system is a **Standalone Desktop Application** built using **Standard Python Tkinter** and a **Local SQLite Database**. It covers:
1.  **Resident Profiling (RIS):** Digital census and household mapping.
2.  **E-Blotter System:** Digital recording and tracking of complaints/incidents.
3.  **Document Issuance:** Automated printing of Clearances and Certifications.
4.  **Analytics Dashboard:** Visualizing crime density and predicting high-risk zones.

### 1.3 Target Users
*   **Barangay Captain:** Main consumer of analytics reports for decision-making.
*   **Barangay Secretary:** Primary data entry user (Residents, Documents).
*   **Barangay Tanods:** End-users of the "Patrol Deployment" assignments.

---

## 🔍 2. Current State Analysis (As-Is Process)

| Process | Current Method (Manual) | Pain Points |
| :--- | :--- | :--- |
| **Resident Retrieval** | Manual search through physical logbooks/Excel. | Slow retrieval; duplicate records; "Indigency" status hard to verify. |
| **Blotter Entry** | Handwritten in an Official Logbook. | Illegible handwriting; records prone to loss/tampering; no search history for repeat offenders. |
| **Clearance Issuance**| Typed in Word, printed, logged in notebook. | No unique control numbers (prone to fraud); manual collection tracking is error-prone. |
| **Patrol Strategy** | Random deployment or based on gut feel. | Inefficient use of manpower; crimes occur in unmonitored areas. |

---

## ⚙️ 3. Functional Requirements

### Module 1: Resident Information System (RIS)
- [ ] **FR-1.1:** Create resident profiles: *Name, Birthdate, Sex, Civil Status, Address (Purok), Occupation, Photo*.
- [ ] **FR-1.2:** Group residents under a unique **Household ID**.
- [ ] **FR-1.3:** Search capability by Name, Alias, or Household ID.
- [ ] **FR-1.4:** Tag residents as *Active, Deceased, Moved Out,* or *Indigent*.

### Module 2: E-Blotter & Case Management
- [ ] **FR-2.1:** Record incident details: *Date/Time, Narrative, Incident Type, Location (Purok)*.
- [ ] **FR-2.2:** Link existing Resident Profiles as **Complainant** or **Respondent** (Suspect).
- [ ] **FR-2.3:** Track case status: *Pending, Amicable Settlement, Escalated to PNP, Closed*.
- [ ] **FR-2.4:** **Recidivist Alert:** Automatically warn the user if a selected Respondent has prior blotter cases.

### Module 3: Document Issuance
- [ ] **FR-3.1:** Auto-generate PDF documents (Clearance, Indigency, Permit) using stored resident data.
- [ ] **FR-3.2:** Auto-assign unique, non-editable **Control Numbers** to prevent fraud.
- [ ] **FR-3.3:** Log Official Receipt (O.R.) Number and Amount Paid.

### Module 4: Intelligence & Analytics (BI Core)
- [ ] **FR-4.1:** **Crime Heatmap:** Color-coded Bar/Pie Chart (Green/Yellow/Red) visualizing incident count per Purok.
- [ ] **FR-4.2:** **Time-Series Analysis:** Chart showing "Most Dangerous Time of Day" based on historical timestamps.
- [ ] **FR-4.3:** **Patrol Recommender:** Text output suggesting: *"Deploy patrol to [Purok X] at [Time Range]"* based on frequency analysis.

### Module 5: System Administration
- [ ] **FR-5.1:** One-Click Database Backup (.SQL/.CSV export).
- [ ] **FR-5.2:** Audit Trail logging sensitive actions (e.g., Deletion of Blotter Case).

---

## 🧱 4. Non-Functional Requirements (NFR)

1.  **UI/UX Design Standards (Best Effort):**
    *   **Visual Consistency:** The application must utilize `tkinter.ttk` (Themed Tkinter) styling to enforce a unified color palette (e.g., Corporate Blue/Slate Gray), consistent font families (Arial/Helvetica), and standardized widget sizing across all modules.
    *   **Visual Hierarchy:** The layout must employ proper **Information Architecture**, using distinct font weights for headers vs. body text, and strategic use of **Whitespace** (padding/margins) to prevent UI clutter common in legacy desktop apps.
    *   **Feedback & Affordance:** Buttons and interactive elements must provide visual feedback (e.g., cursor changes, active states). Long-running processes (like generating analytics) must display a progress bar or "Loading" cursor to prevent perceived freezing.
    *   **Constraint:** While limited by standard Tkinter's lack of advanced rendering (shadows/animations), the design must prioritize **Readability** and **Ease of Navigation** over aesthetic flair.

2.  **Performance:** Search queries (e.g., finding a resident) must execute and render within **2 seconds** for a database of up to 10,000 records.

3.  **Reliability:** The system must function **100% Offline** (Air-gapped), requiring no internet connection for core CRUD or Analytics operations.

4.  **Security:** 
    *   User passwords must be hashed using **SHA-256** before database storage.
    *   The system must prevent SQL Injection via parameterization of all database queries.

5.  **Deployment & Compatibility:** 
    *   The application must be executable on **Windows 10/11** environments.
    *   It must run using the **Standard Python Library** (no requirement for `pip install` of complex external GUI frameworks like Qt or Kivy) to ensure easy deployment on low-spec Barangay hardware.

---

## 🗄️ 5. Data Requirements (Database Schema)

The database will follow **3rd Normal Form (3NF)** using **SQLite**.

### I. Master Data
*   **Residents:** `res_id` (PK), `first_name`, `last_name`, `purok_id`, `is_indigent`, `photo_blob`
*   **Households:** `hh_id` (PK), `house_number`, `street_name`
*   **Puroks:** `purok_id` (PK), `purok_name`, `assigned_tanod_leader`

### II. Transactions (Blotter)
*   **IncidentTypes:** `type_id` (PK), `name` (e.g., Theft, Gossip), `severity` (1-5)
*   **BlotterCases:** `case_id` (PK), `date_time`, `narrative`, `purok_id` (FK), `status`
*   **CaseInvolvement:** `link_id` (PK), `case_id` (FK), `res_id` (FK), `role` (Suspect/Victim)

### III. Logs
*   **DocLogs:** `doc_id` (PK), `res_id` (FK), `doc_type`, `amount`, `or_number`
*   **AuditLogs:** `log_id` (PK), `user_id`, `action`, `timestamp`

---

## 🧠 6. Business Intelligence Logic (The "Smart" Features)

### 6.1 The Hotspot Logic
**Goal:** Determine the urgency level of a Purok on the Dashboard.
1.  **Query:** Select `BlotterCases` from the last 30 days.
2.  **Group:** By `purok_id`.
3.  **Rule:**
    *   Count = 0: 🟢 **Green (Safe)**
    *   Count 1-3: 🟡 **Yellow (Caution)**
    *   Count > 3: 🔴 **Red (Hotspot)**

### 6.2 The Recidivism Logic
**Goal:** Flag repeat offenders during data entry.
1.  **Trigger:** User selects a Resident for the "Respondent" field.
2.  **Check:** Query `CaseInvolvement` where `res_id = SelectedID` AND `role = 'Respondent'`.
3.  **Alert:** If `Count > 0`, display warning: *"⚠️ Subject has prior blotter records."*

---

## 🧪 7. Software & Hardware Stack

*   **Language:** Python 3.10+ (Standard Library)
*   **GUI Framework:** Tkinter & Tkinter.ttk (Native Python GUI)
*   **Database:** SQLite3 (Embedded)
*   **Testing Framework:** `pytest` (For Unit and Integration Testing)
*   **Analytics:** Pandas (Data Processing), Matplotlib (Charts)
*   **Reporting:** ReportLab (PDF Generation)
*   **Minimum Specs:** Windows 10/11, Core i3, 4GB RAM.

---

## 📐 8. Quality Assurance & Development Methodology

The project strictly adheres to **Test-Driven Development (TDD)** principles to ensure algorithmic accuracy and system stability.

1.  **Red-Green-Refactor Cycle:**
    *   **Red:** Write a failing test case for a specific function (e.g., `calculate_crime_density()`).
    *   **Green:** Write the minimal Python code required to pass the test.
    *   **Refactor:** Optimize the code while ensuring tests still pass.

2.  **Scope of Testing (using `pytest`):**
    *   **Business Logic:** All analytics algorithms (Heatmap, Time-Series) must be unit-tested to ensure accurate statistical output.
    *   **Database Interactions:** Integration tests will verify that CRUD operations (Create Resident, Log Incident) correctly modify the SQLite database without integrity errors.
    *   **Validation Logic:** Input validation rules (e.g., preventing duplicate Control Numbers) must be verified via automated tests.

---

## ✅ 9. Sign-off Criteria

The project is complete when:
1.  All Unit Tests pass (`pytest` execution shows 100% success).
2.  A user can add a Resident and print a Clearance PDF using the native UI.
3.  A user can log a Blotter Incident linked to that Resident.
4.  The Dashboard Graph updates automatically when a new Blotter is added.
5.  The System generates a "Monthly Peace & Order" PDF Report.