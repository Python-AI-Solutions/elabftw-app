# Testing Guide for eLabFTW Fiber Photometry Tool

This document provides comprehensive testing procedures for all three user journeys.

## Prerequisites

### Environment Setup

1. **Python Environment**
   ```bash
   # Using pixi (recommended)
   pixi add streamlit elabapi-python

   # Or using pip
   pip install streamlit elabapi-python
   ```

2. **eLabFTW Configuration**
   ```bash
   export ELABFTW_API_KEY="your_api_key_here"
   export ELABFTW_URL="https://your-elabftw.com"
   export ELABFTW_VERIFY_SSL="true"  # Optional
   ```

3. **Test Data**
   - Access to eLabFTW instance
   - At least 3 test experiments:
     - One with partial metadata (for Journey A)
     - One blank (for Journey C)
     - One for creating fresh (Journey B)

## Running the App

```bash
cd elabftw-app-tool/streamlit_app
streamlit run Home.py
```

The app should open at `http://localhost:8501`

## Test Plan

### Phase 1: Home Page Navigation Tests

#### Test 1.1: Home Page Load
**Objective**: Verify home page loads correctly with all sections

**Steps**:
1. Launch app with `streamlit run Home.py`
2. Observe home page rendering

**Expected Results**:
- ✅ Main title: "eLabFTW Fiber Photometry Tool"
- ✅ Subtitle about NWB compliance
- ✅ Three journey cards visible (A, B, C)
- ✅ Each card has distinct color gradient
- ✅ Configuration status shown at bottom
- ✅ Sidebar with documentation links

**Pass Criteria**: All elements render without errors

#### Test 1.2: API Configuration Status
**Objective**: Verify API configuration check works

**Steps**:
1. Run with API credentials configured
2. Check "Configuration Status" section
3. Run without credentials
4. Check status again

**Expected Results**:
- ✅ With credentials: Green success message with server URL
- ✅ Without credentials: Red error message with setup instructions
- ✅ If elabapi-python missing: Warning about installation

**Pass Criteria**: Status accurately reflects configuration state

#### Test 1.3: Journey Navigation Buttons
**Objective**: Verify navigation buttons work

**Steps**:
1. Click "Start Journey A" button
2. Verify navigation to Journey A page
3. Navigate back to Home
4. Repeat for Journey B
5. Repeat for Journey C

**Expected Results**:
- ✅ Each button navigates to correct page
- ✅ Pages load without errors
- ✅ Browser back button returns to Home

**Pass Criteria**: All three navigation paths work

---

### Phase 2: Journey A Testing (Validate & Fix)

#### Test 2.1: Load Existing Experiment
**Objective**: Verify experiment loading functionality

**Prerequisites**:
- Create test experiment in eLabFTW with ID (e.g., ID=1)
- Add some but not all required metadata fields

**Steps**:
1. Navigate to Journey A
2. Enter test experiment ID
3. Click "Load Experiment"

**Expected Results**:
- ✅ Experiment info displayed (ID, title, created/modified dates)
- ✅ Current metadata shown in expander
- ✅ "Experiment loaded successfully" message

**Pass Criteria**: Experiment loads without errors

#### Test 2.2: Validation with Missing Required Fields
**Objective**: Verify validation identifies missing fields

**Prerequisites**:
- Experiment loaded from Test 2.1
- Experiment missing ≥5 required fields

**Steps**:
1. After loading experiment, observe validation results
2. Review "Validation Results" section
3. Check error messages

**Expected Results**:
- ✅ Red error box showing number of missing fields
- ✅ Each missing field listed by name
- ✅ Warning box for any data range issues
- ✅ Clear distinction between errors and warnings

**Pass Criteria**: All missing required fields correctly identified

#### Test 2.3: Fill Missing Fields
**Objective**: Verify form for missing fields works

**Steps**:
1. Scroll to "Fill Missing Fields" section
2. Observe form fields
3. Fill in all missing fields with valid data
4. Click "Update Experiment"

**Expected Results**:
- ✅ Form shows only missing fields (not all 45)
- ✅ Smart input types (date picker for dates, number input for numbers)
- ✅ Help text visible for each field
- ✅ Required field indicators shown

**Pass Criteria**: Form renders correctly with appropriate input types

#### Test 2.4: Update Experiment
**Objective**: Verify experiment update via API

**Steps**:
1. Fill missing fields from Test 2.3
2. Click "Update Experiment" button
3. Wait for API call completion

**Expected Results**:
- ✅ Success message: "Experiment updated successfully!"
- ✅ Balloons animation
- ✅ Link to view experiment in eLabFTW
- ✅ Validation re-runs automatically
- ✅ No errors remaining

**Pass Criteria**: Experiment updates successfully and validation passes

#### Test 2.5: Already Complete Experiment
**Objective**: Verify behavior with complete metadata

**Prerequisites**:
- Experiment with all 18 required fields filled

**Steps**:
1. Load complete experiment
2. Observe validation results

**Expected Results**:
- ✅ Green success box: "This experiment meets all requirements!"
- ✅ Checkmark icon shown
- ✅ No missing fields form displayed
- ✅ Option to export metadata as JSON

**Pass Criteria**: Complete experiment correctly identified

---

### Phase 3: Journey B Testing (Create New Entry)

#### Test 3.1: Form Load and Structure
**Objective**: Verify comprehensive form renders correctly

**Steps**:
1. Navigate to Journey B
2. Observe form structure
3. Scroll through all sections

**Expected Results**:
- ✅ Six collapsible sections (groups)
- ✅ 45 total fields across all sections
- ✅ Required fields marked with *
- ✅ Help text on hover/tooltip for each field

**Pass Criteria**: All 45 fields present and organized correctly

#### Test 3.2: Smart Input Types
**Objective**: Verify correct input widgets for each field type

**Steps**:
1. Open each form section
2. Check input types for various fields

**Expected Results**:
- ✅ Text inputs: Subject ID, Species, Experimenter
- ✅ Date pickers: Surgery Date, Session Date
- ✅ Time picker: Session Time
- ✅ Number inputs: Age, Coordinates, Wavelengths, Diameters
- ✅ Selectboxes: Sex, Indicator, Behavioral Task
- ✅ Text areas: Notes, Description

**Pass Criteria**: All input types appropriate for data type

#### Test 3.3: Smart Defaults
**Objective**: Verify pre-filled default values

**Steps**:
1. Check default values without filling anything

**Expected Results**:
- ✅ Species: "Mus musculus"
- ✅ Excitation Wavelength: 470 nm
- ✅ Emission Wavelength: 525 nm
- ✅ Some fields blank (requiring user input)

**Pass Criteria**: Defaults present for common values

#### Test 3.4: Real-Time Validation
**Objective**: Verify validation before submission

**Steps**:
1. Scroll to bottom without filling required fields
2. Click "Submit to eLabFTW"
3. Observe error messages

**Expected Results**:
- ✅ Red error box listing missing required fields
- ✅ Submission blocked
- ✅ Clear guidance on what to fix

**Pass Criteria**: Cannot submit incomplete form

#### Test 3.5: Export to JSON
**Objective**: Verify JSON export functionality

**Steps**:
1. Fill some fields (not all)
2. Click "Save to JSON" in sidebar
3. Download and inspect JSON file

**Expected Results**:
- ✅ JSON file downloads successfully
- ✅ File named: `fiber_photometry_metadata_YYYYMMDD_HHMMSS.json`
- ✅ Contains all filled fields
- ✅ Valid JSON format
- ✅ Empty fields omitted or empty strings

**Pass Criteria**: JSON export works and format is valid

#### Test 3.6: Import from JSON
**Objective**: Verify JSON import pre-fills form

**Steps**:
1. Use JSON file from Test 3.5
2. Click "Load from JSON" in sidebar
3. Upload the JSON file
4. Observe form

**Expected Results**:
- ✅ Success message: "Metadata loaded successfully!"
- ✅ All previously filled fields now populated
- ✅ Form state restored exactly
- ✅ Can continue editing

**Pass Criteria**: Form pre-populates correctly from JSON

#### Test 3.7: Submit to eLabFTW
**Objective**: Verify submission creates experiment

**Prerequisites**:
- API credentials configured
- All 18 required fields filled

**Steps**:
1. Fill all required fields
2. Click "Submit to eLabFTW"
3. Wait for API call

**Expected Results**:
- ✅ Success message with experiment ID
- ✅ Link to view experiment in eLabFTW
- ✅ Balloons animation
- ✅ Option to create another entry
- ✅ JSON export of submitted data available

**Pass Criteria**: Experiment created successfully in eLabFTW

#### Test 3.8: Submit Without API (Local Save)
**Objective**: Verify fallback to local save when API unavailable

**Prerequisites**:
- Remove API credentials

**Steps**:
1. Fill form completely
2. Click "Submit to eLabFTW"

**Expected Results**:
- ✅ Warning: API not configured
- ✅ JSON file saved locally instead
- ✅ Success message about local save
- ✅ Data preserved

**Pass Criteria**: Graceful fallback to local save

---

### Phase 4: Journey C Testing (Add Template)

#### Test 4.1: Template Preview
**Objective**: Verify template loads and displays correctly

**Steps**:
1. Navigate to Journey C
2. Observe "Preview Template" section
3. Check sidebar statistics

**Expected Results**:
- ✅ Template loads automatically
- ✅ Statistics displayed: 45 total, 18 required, 27 optional, 6 groups
- ✅ Six group names listed
- ✅ Expandable JSON preview available

**Pass Criteria**: Template loads with correct statistics

#### Test 4.2: Load Blank Experiment
**Objective**: Verify blank experiment detection

**Prerequisites**:
- Create blank experiment in eLabFTW (no metadata)

**Steps**:
1. Enter blank experiment ID
2. Click "Load Experiment"
3. Observe experiment info section

**Expected Results**:
- ✅ Experiment info displayed
- ✅ Green success box: "This experiment is blank and ready for the template!"
- ✅ No current metadata shown

**Pass Criteria**: Blank experiment correctly identified

#### Test 4.3: Load Experiment with Existing Metadata
**Objective**: Verify detection of non-blank experiment

**Prerequisites**:
- Experiment with some metadata fields

**Steps**:
1. Enter experiment ID
2. Click "Load Experiment"

**Expected Results**:
- ✅ Info box: "This experiment already has X fields"
- ✅ Warning about merging with existing fields
- ✅ Current metadata viewable in expander

**Pass Criteria**: Existing metadata detected and displayed

#### Test 4.4: Apply Template to Blank Experiment
**Objective**: Verify template injection works

**Prerequisites**:
- Blank experiment loaded from Test 4.2

**Steps**:
1. Click "Apply Template to Experiment" button
2. Wait for API call
3. Observe success section

**Expected Results**:
- ✅ Success message with experiment ID
- ✅ Balloons animation
- ✅ Link to open experiment in eLabFTW
- ✅ "What's next?" guidance shown
- ✅ Updated metadata displayed in expander

**Pass Criteria**: Template applied successfully

#### Test 4.5: Verify Template in eLabFTW
**Objective**: Verify template structure in eLabFTW UI

**Prerequisites**:
- Completed Test 4.4

**Steps**:
1. Click link to open experiment in eLabFTW
2. Navigate to metadata section in eLabFTW
3. Inspect fields and groups

**Expected Results**:
- ✅ All 45 fields present
- ✅ Organized into 6 groups
- ✅ Group names match template
- ✅ Required fields marked with * in eLabFTW
- ✅ Field types correct (text, number, date, etc.)
- ✅ Help text visible in eLabFTW

**Pass Criteria**: Template structure matches JSON in eLabFTW

#### Test 4.6: Apply Template to Another Experiment
**Objective**: Verify reset functionality

**Steps**:
1. After successful template application
2. Click "Apply Template to Another Experiment"
3. Observe app state

**Expected Results**:
- ✅ Form resets to Step 2 (Select Target Experiment)
- ✅ Previous experiment data cleared
- ✅ Can enter new experiment ID
- ✅ Template still loaded in sidebar

**Pass Criteria**: Reset works correctly

---

### Phase 5: Integration Tests

#### Test 5.1: Cross-Journey Workflow
**Objective**: Test complete workflow across all journeys

**Steps**:
1. **Journey C**: Create blank experiment, apply template
2. **Journey A**: Load same experiment, verify validation passes
3. **Journey B**: Fill another experiment, submit
4. **Journey A**: Load Journey B experiment, verify validation

**Expected Results**:
- ✅ Journey C → Journey A: Template structure recognized, all fields valid
- ✅ Journey B → Journey A: Form data correctly validated
- ✅ Data integrity maintained across journeys

**Pass Criteria**: All journeys interoperate correctly

#### Test 5.2: Session State Persistence
**Objective**: Verify session state across page navigation

**Steps**:
1. Start Journey B, fill 10 fields
2. Navigate to Home
3. Navigate back to Journey B

**Expected Results**:
- ⚠️ **Note**: Streamlit resets session state on page change
- ✅ Form is reset (expected behavior)
- ✅ Use JSON export/import for persistence

**Pass Criteria**: Behavior consistent with Streamlit conventions

#### Test 5.3: Multiple Browser Tabs
**Objective**: Verify independent sessions in multiple tabs

**Steps**:
1. Open app in Tab 1, start Journey A
2. Open app in Tab 2, start Journey B
3. Work in both tabs simultaneously

**Expected Results**:
- ✅ Each tab has independent session
- ✅ No interference between tabs
- ✅ API calls from both tabs work

**Pass Criteria**: Tabs operate independently

---

### Phase 6: Error Handling Tests

#### Test 6.1: Invalid Experiment ID
**Objective**: Verify error handling for non-existent experiments

**Steps**:
1. Navigate to Journey A or C
2. Enter invalid experiment ID (e.g., 999999)
3. Click "Load Experiment"

**Expected Results**:
- ✅ Red error message: "Failed to load experiment"
- ✅ API error details shown
- ✅ App remains functional
- ✅ Can try again with different ID

**Pass Criteria**: Graceful error handling

#### Test 6.2: Network/API Errors
**Objective**: Verify behavior when API is unreachable

**Steps**:
1. Configure invalid ELABFTW_URL
2. Attempt any API operation

**Expected Results**:
- ✅ Error message about API failure
- ✅ Timeout handled gracefully
- ✅ No app crash
- ✅ User guidance provided

**Pass Criteria**: Network errors handled gracefully

#### Test 6.3: Invalid API Key
**Objective**: Verify authentication error handling

**Steps**:
1. Configure invalid ELABFTW_API_KEY
2. Attempt to load experiment

**Expected Results**:
- ✅ Error message about authentication
- ✅ Suggestion to check API key
- ✅ No sensitive data leaked in error

**Pass Criteria**: Auth errors handled securely

#### Test 6.4: Malformed Template JSON
**Objective**: Verify error handling for corrupted template

**Steps**:
1. Temporarily corrupt template JSON file
2. Launch Journey C

**Expected Results**:
- ✅ Error message in sidebar
- ✅ App stops gracefully
- ✅ Clear guidance about template file issue

**Pass Criteria**: Template errors caught and reported

---

### Phase 7: Validation Tests

#### Test 7.1: Required Field Validation
**Objective**: Verify all 18 required fields enforced

**Steps**:
1. Use Journey B
2. Fill all fields except each required field one at a time
3. Attempt submission

**Expected Results**:
- ✅ Submission blocked for each missing required field
- ✅ Specific field name shown in error
- ✅ Error clears when field filled

**Pass Criteria**: All 18 required fields enforced

#### Test 7.2: Data Range Validation
**Objective**: Verify coordinate and wavelength ranges

**Steps**:
1. Enter coordinates outside -10 to 10 mm range
2. Enter wavelengths outside 300-800 nm range
3. Enter NA outside 0.1-1.0 range

**Expected Results**:
- ✅ Journey A: Warnings shown in validation results
- ✅ Journey B: Form validation prevents submission or shows warnings
- ✅ Guidance on valid ranges provided

**Pass Criteria**: Range validation works for all validated fields

#### Test 7.3: Field Type Validation
**Objective**: Verify input type constraints

**Steps**:
1. Attempt to enter text in number fields
2. Attempt to enter invalid dates
3. Check selectbox options

**Expected Results**:
- ✅ Number fields only accept numeric input
- ✅ Date pickers prevent invalid dates
- ✅ Selectboxes restrict to predefined options

**Pass Criteria**: Input types enforce data constraints

---

### Phase 8: UI/UX Tests

#### Test 8.1: Responsive Design
**Objective**: Verify layout on different screen sizes

**Steps**:
1. Test on desktop (1920x1080)
2. Test on tablet size (768px width)
3. Resize browser window dynamically

**Expected Results**:
- ✅ Home page cards stack on narrow screens
- ✅ Forms remain usable on tablet
- ✅ No horizontal scrolling required
- ✅ Buttons and inputs scale appropriately

**Pass Criteria**: App usable on tablet and desktop

#### Test 8.2: Visual Feedback
**Objective**: Verify user feedback for actions

**Steps**:
1. Perform actions in each journey
2. Observe loading states, success messages, errors

**Expected Results**:
- ✅ Spinners shown during API calls
- ✅ Success messages green with checkmarks
- ✅ Error messages red with X icons
- ✅ Info messages blue with info icons
- ✅ Balloons animation for major successes

**Pass Criteria**: Clear visual feedback for all actions

#### Test 8.3: Navigation Clarity
**Objective**: Verify clear workflow progression

**Steps**:
1. Complete each journey
2. Observe step numbering and progress

**Expected Results**:
- ✅ Steps clearly numbered (Step 1, Step 2, etc.)
- ✅ Current step highlighted or indicated
- ✅ Cannot proceed to next step without completing current
- ✅ Back navigation possible

**Pass Criteria**: Workflow progression intuitive

---

## Test Checklist Summary

### Critical Tests (Must Pass)
- [ ] Home page loads without errors
- [ ] API configuration status accurate
- [ ] Journey A: Load experiment
- [ ] Journey A: Validation identifies missing fields
- [ ] Journey A: Update experiment
- [ ] Journey B: Form renders all 45 fields
- [ ] Journey B: Submit creates experiment
- [ ] Journey C: Template loads correctly
- [ ] Journey C: Apply template to blank experiment
- [ ] Journey C: Verify template in eLabFTW
- [ ] Error handling for invalid experiment IDs
- [ ] Error handling for API failures

### Important Tests (Should Pass)
- [ ] Navigation between journeys
- [ ] Journey A: Already complete experiment
- [ ] Journey B: Export to JSON
- [ ] Journey B: Import from JSON
- [ ] Journey B: Local save without API
- [ ] Journey C: Detect existing metadata
- [ ] Data range validation warnings
- [ ] Invalid API key handling

### Nice to Have Tests (Quality)
- [ ] Responsive design on tablet
- [ ] Visual feedback (spinners, messages)
- [ ] Session state behavior documented
- [ ] Multiple tabs work independently
- [ ] Template JSON corruption handling

## Reporting Issues

When reporting test failures, include:
1. **Test ID** (e.g., Test 2.3)
2. **Steps to reproduce**
3. **Expected vs. actual behavior**
4. **Screenshots** if UI-related
5. **Console errors** from browser dev tools
6. **API logs** if relevant
7. **Environment**: Python version, Streamlit version, OS

## Automated Testing (Future)

Consider adding:
- Selenium tests for UI workflows
- Unit tests for validation functions
- API mocking for offline testing
- CI/CD integration for regression testing

## Version

Testing Guide Version: 1.0.0
Last Updated: 2025-11-04
Applies to: elabftw-app-tool v1.0.0
