# eLabFTW Template Structure

This document explains how the LabArchives experiment structure from the Tejeda Lab was ported to eLabFTW.

## Structure Mapping

Based on the analysis in `first-api-response.md`, the following mapping was used:

| LabArchives Concept | eLabFTW Equivalent | Description |
|---------------------|-------------------|-------------|
| Notebook | Server | One eLabFTW server per lab |
| Experiment Directory | Category | Top-level organization (Behavior, Surgeries, etc.) |
| Cohort Directory | Tag | Reusable labels for cohorts and sessions |
| Widget (Form) | Template | Data entry forms with extra fields |

## Original LabArchives Structure

```
Experiment 1/
├── Behavior/
│   ├── Cohort 1/
│   │   ├── Baseline
│   │   ├── Training Day 1
│   │   ├── Training Day 2
│   │   └── Testing
│   └── Cohort 2/
│       └── ...
├── Histology/
├── Metadata/
├── Photometry/
└── Surgeries/
    ├── Cohort 1/
    │   └── Implant and Injection
    └── Cohort 2/
        ├── Implant
        └── Injection
```

## eLabFTW Implementation

### Categories (5 total)
Categories replace the top-level experiment directories:

| Category | Color | Purpose |
|----------|-------|---------|
| Behavior | #1abc9c | Behavior experiment entries |
| Histology | #3498db | Histology data entries |
| Metadata | #9b59b6 | Experiment metadata entries |
| Photometry | #e74c3c | Fiber photometry data entries |
| Surgeries | #f39c12 | Surgery data entries |

### Tags (15 total)
Tags replace the cohort directories and session types:

**Cohort Tags:**
- Cohort 1, Cohort 2, Cohort 3, Cohort 4, Cohort 5

**Session Tags:**
- Baseline
- Training Day 1, Training Day 2, Training Day 3, Training Day 4, Training Day 5
- Testing

**Surgery Tags:**
- Implant
- Injection
- Implant and Injection

### Templates (2 total)
Templates replace the LabArchives widgets (forms):

#### Surgery Data Entry Template
Based on `docs/surgery.html`, includes:
- **General Info**: Date, Description, Stereotax Number
- **Surgery Type**: Intracranial Injection, Implant, Other
- **Injection Method**: Glass Pipette, Syringe Needle, Other
- **Viral Vectors 1-4**: Name, Source, Cat#, Lot#, Titer, Dilution
- **Injection Sites 1-5**: Brain Area, Hemisphere, AP/ML/DV, Virus, Volume, Speed
- **Implant Sites 1-3**: Brain Area, Hemisphere, AP/ML/DV
- **Subject Details**: ID, Strain, Cage, Genotype, Sex, DOB, Weight, Negate ML
- **Notes**: Injection, Implant, Surgery notes

#### Behavior Session Template
Based on `docs/behavior.html`, includes:
- **Session Info**: Date, Time, Personnel, Room, Experiment, Subjects, Manipulation, Video Path, AnyMaze Protocol, Cue Info, Reward Info
- **Subject Details**: ID, Weight, Reward Consumed, Shock Intensity, Box Number, Novel Object Side, Sucrose Side, Notes

## Key Differences from LabArchives

1. **Single Subject Per Entry**: eLabFTW doesn't support dynamic/repeating field groups, so each experiment entry represents one subject. For multiple subjects, create multiple entries.

2. **Flat Tag Structure**: Unlike LabArchives' nested directories, eLabFTW uses a flat tag system. Combine tags to represent hierarchy (e.g., "Cohort 1" + "Training Day 1").

3. **Pre-defined Field Slots**: The original HTML forms had dynamic tables for multiple mice. In eLabFTW, we pre-define slots (4 viruses, 5 injections, 3 implants) based on typical usage.

## Usage Workflow

1. **Create New Experiment**
   - Go to Experiments → Create New
   - Select appropriate **Category** (e.g., "Surgeries" or "Behavior")
   - Select appropriate **Template** (e.g., "Surgery Data Entry")

2. **Organize with Tags**
   - Add **Cohort tag** (e.g., "Cohort 1")
   - Add **Session tag** if applicable (e.g., "Training Day 1")

3. **Fill in Data**
   - Complete the extra fields in the template
   - One entry per subject

## Files

| File | Description |
|------|-------------|
| `experiment_structure.json` | Categories and tags configuration |
| `surgery_template.json` | Surgery form extra fields (102 fields) |
| `behavior_template.json` | Behavior form extra fields (19 fields) |

## Running the Setup

```bash
python create_templates.py
```

This will prompt for an API key and create all categories, tags, and templates in eLabFTW.
