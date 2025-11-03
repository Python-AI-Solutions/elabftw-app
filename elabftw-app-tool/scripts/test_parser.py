#!/usr/bin/env python3
"""
Test script for eLabFTW metadata parser.

This script tests the parser with mock data to ensure correct field mapping
without requiring access to a live eLabFTW instance.

Author: elabftw-app
Created: 2025-11-03
"""

import json
from parse_elabftw_metadata import ELabFTWMetadataParser


def create_mock_metadata():
    """Create mock eLabFTW metadata for testing."""
    return {
        "extra_fields": {
            "Subject ID": {"value": "M001"},
            "Species": {"value": "Mus musculus"},
            "Sex": {"value": "M"},
            "Age (days)": {"value": "90"},
            "Strain": {"value": "C57BL/6J"},
            "Genotype": {"value": "Th-Cre+/-"},
            "Weight (grams)": {"value": "25.3"},
            "Surgery Date": {"value": "2024-01-10"},
            "Indicator Label": {"value": "GCaMP6f"},
            "Injection Location": {"value": "VTA"},
            "Injection AP (mm)": {"value": "3.0"},
            "Injection ML (mm)": {"value": "2.0"},
            "Injection DV (mm)": {"value": "4.5"},
            "Viral Vector Name": {"value": "AAV9-hSyn-GCaMP6f"},
            "Viral Titer": {"value": "1e13 GC/mL"},
            "Injection Volume (nL)": {"value": "500"},
            "Fiber Implant Depth (mm)": {"value": "4.2"},
            "Session ID": {"value": "session_20240115_M001"},
            "Session Date": {"value": "2024-01-15"},
            "Session Time": {"value": "14:30"},
            "Session Description": {"value": "Baseline recording"},
            "Experimenter": {"value": "John Doe"},
            "Laboratory": {"value": "Neuroscience Lab"},
            "Institution": {"value": "NIH NIMH"},
            "Optical Fiber Model": {"value": "Doric MFC_400/430-0.48"},
            "Fiber Core Diameter (μm)": {"value": "400"},
            "Fiber Numerical Aperture": {"value": "0.39"},
            "Excitation Wavelength (nm)": {"value": "470"},
            "Emission Wavelength (nm)": {"value": "520"},
            "Dichroic Mirror Cut-on (nm)": {"value": "495"},
            "Emission Filter Center (nm)": {"value": "525"},
            "Emission Filter Bandwidth (nm)": {"value": "50"},
            "LED Power (mW)": {"value": "5.0"},
            "PMT Gain": {"value": "1000"},
            "Recording Location": {"value": "VTA"},
            "Channel Name": {"value": "GCaMP6f_470nm"},
            "Sampling Rate (Hz)": {"value": "1000"},
            "Protocol Name": {"value": "Standard FP Protocol v2"},
            "Data File Path": {"value": "/data/photometry/M001/"},
            "Behavioral Task": {"value": "Freely moving"},
            "Drug Treatment": {"value": ""},
            "Notes": {"value": "Animal behaving normally"},
            "Analysis Status": {"value": "Pending"},
            "Quality Control": {"value": "Pass"}
        }
    }


def test_field_extraction():
    """Test that all fields are correctly extracted."""
    print("=" * 60)
    print("Test 1: Field Extraction")
    print("=" * 60)

    # Create mock parser (no API needed for metadata parsing)
    parser = ELabFTWMetadataParser(
        api_key="mock_key",
        elabftw_url="https://mock.elabftw.com",
        verify_ssl=False
    )

    mock_metadata = create_mock_metadata()
    nwb_metadata = parser.map_to_nwb_metadata(mock_metadata)

    # Check subject metadata
    assert nwb_metadata['subject']['subject_id'] == 'M001', "Subject ID mismatch"
    assert nwb_metadata['subject']['species'] == 'Mus musculus', "Species mismatch"
    assert nwb_metadata['subject']['sex'] == 'M', "Sex mismatch"
    assert nwb_metadata['subject']['age'] == 'P90D', "Age conversion failed"
    assert nwb_metadata['subject']['strain'] == 'C57BL/6J', "Strain mismatch"

    print("✅ Subject metadata: PASS")

    # Check indicator metadata
    assert nwb_metadata['indicator']['label'] == 'GCaMP6f', "Indicator label mismatch"
    assert nwb_metadata['indicator']['injection_location'] == 'VTA', "Injection location mismatch"
    assert nwb_metadata['indicator']['injection_coordinates_in_mm'] == (3.0, 2.0, 4.5), \
        "Injection coordinates mismatch"

    print("✅ Indicator metadata: PASS")

    # Check session metadata
    assert nwb_metadata['session']['session_id'] == 'session_20240115_M001', "Session ID mismatch"
    assert nwb_metadata['session']['session_start_time'] == '2024-01-15T14:30:00', \
        "Session timestamp conversion failed"
    assert nwb_metadata['session']['experimenter'] == ['John Doe'], "Experimenter mismatch"

    print("✅ Session metadata: PASS")

    # Check device metadata
    assert nwb_metadata['optical_fiber']['core_diameter_in_um'] == 400.0, \
        "Fiber diameter mismatch"
    assert nwb_metadata['optical_fiber']['numerical_aperture'] == 0.39, "NA mismatch"
    assert nwb_metadata['excitation_source']['excitation_wavelength_in_nm'] == 470.0, \
        "Excitation wavelength mismatch"
    assert nwb_metadata['photodetector']['detected_wavelength_in_nm'] == 520.0, \
        "Emission wavelength mismatch"

    print("✅ Device metadata: PASS")

    # Check FiberPhotometryTable metadata
    assert nwb_metadata['fiber_photometry_table']['location'] == 'VTA', \
        "Recording location mismatch"

    print("✅ FiberPhotometryTable metadata: PASS")

    print("\n✅ ALL FIELD EXTRACTION TESTS PASSED\n")


def test_validation():
    """Test validation functions."""
    print("=" * 60)
    print("Test 2: Validation")
    print("=" * 60)

    parser = ELabFTWMetadataParser(
        api_key="mock_key",
        elabftw_url="https://mock.elabftw.com",
        verify_ssl=False
    )

    # Test with complete metadata (should pass)
    complete_metadata = create_mock_metadata()
    errors = parser.validate_required_fields(complete_metadata)
    assert len(errors) == 0, f"Complete metadata failed validation: {errors}"
    print("✅ Complete metadata validation: PASS")

    # Test with missing required field
    incomplete_metadata = create_mock_metadata()
    del incomplete_metadata['extra_fields']['Subject ID']
    errors = parser.validate_required_fields(incomplete_metadata)
    assert len(errors) > 0, "Missing required field not detected"
    assert any('Subject ID' in error for error in errors), "Subject ID error not reported"
    print("✅ Missing required field detection: PASS")

    # Test with empty required field
    empty_field_metadata = create_mock_metadata()
    empty_field_metadata['extra_fields']['Sex']['value'] = ''
    errors = parser.validate_required_fields(empty_field_metadata)
    assert len(errors) > 0, "Empty required field not detected"
    assert any('Sex' in error for error in errors), "Sex error not reported"
    print("✅ Empty required field detection: PASS")

    # Test data range validation
    good_metadata = create_mock_metadata()
    warnings = parser.validate_data_ranges(good_metadata)
    assert len(warnings) == 0, f"Good data produced warnings: {warnings}"
    print("✅ Valid data ranges: PASS")

    # Test out-of-range coordinate
    bad_coordinate_metadata = create_mock_metadata()
    bad_coordinate_metadata['extra_fields']['Injection AP (mm)']['value'] = '15.0'
    warnings = parser.validate_data_ranges(bad_coordinate_metadata)
    assert len(warnings) > 0, "Out-of-range coordinate not detected"
    assert any('Injection AP' in warning for warning in warnings), \
        "Injection AP warning not reported"
    print("✅ Out-of-range coordinate detection: PASS")

    # Test out-of-range wavelength
    bad_wavelength_metadata = create_mock_metadata()
    bad_wavelength_metadata['extra_fields']['Excitation Wavelength (nm)']['value'] = '1000'
    warnings = parser.validate_data_ranges(bad_wavelength_metadata)
    assert len(warnings) > 0, "Out-of-range wavelength not detected"
    assert any('Excitation Wavelength' in warning for warning in warnings), \
        "Excitation wavelength warning not reported"
    print("✅ Out-of-range wavelength detection: PASS")

    print("\n✅ ALL VALIDATION TESTS PASSED\n")


def test_edge_cases():
    """Test edge cases and optional fields."""
    print("=" * 60)
    print("Test 3: Edge Cases")
    print("=" * 60)

    parser = ELabFTWMetadataParser(
        api_key="mock_key",
        elabftw_url="https://mock.elabftw.com",
        verify_ssl=False
    )

    # Test with minimal metadata (only required fields)
    minimal_metadata = {
        "extra_fields": {
            "Subject ID": {"value": "M002"},
            "Species": {"value": "Mus musculus"},
            "Sex": {"value": "F"},
            "Surgery Date": {"value": "2024-01-05"},
            "Indicator Label": {"value": "GCaMP7s"},
            "Injection Location": {"value": "NAc"},
            "Injection AP (mm)": {"value": "1.2"},
            "Injection ML (mm)": {"value": "0.8"},
            "Injection DV (mm)": {"value": "5.0"},
            "Session ID": {"value": "session_002"},
            "Session Date": {"value": "2024-01-20"},
            "Session Time": {"value": "10:00"},
            "Experimenter": {"value": "Jane Smith"},
            "Fiber Core Diameter (μm)": {"value": "200"},
            "Fiber Numerical Aperture": {"value": "0.22"},
            "Excitation Wavelength (nm)": {"value": "405"},
            "Emission Wavelength (nm)": {"value": "480"},
            "Recording Location": {"value": "NAc"}
        }
    }

    nwb_metadata = parser.map_to_nwb_metadata(minimal_metadata)

    # Check that optional fields are None or have defaults
    assert nwb_metadata['subject']['age'] is None, "Age should be None when not provided"
    assert nwb_metadata['subject']['strain'] is None, "Strain should be None when not provided"
    assert nwb_metadata['viral_vector']['name'] is None, \
        "Viral vector should be None when not provided"
    assert nwb_metadata['dichroic_mirror'] is None, \
        "Dichroic mirror should be None when not provided"
    assert nwb_metadata['emission_filter'] is None, \
        "Emission filter should be None when not provided"

    print("✅ Optional fields handling: PASS")

    # Test age conversion edge cases
    assert parser._convert_age_to_iso8601(None) is None, "None age should return None"
    assert parser._convert_age_to_iso8601('') is None, "Empty age should return None"
    assert parser._convert_age_to_iso8601(0) == 'P0D', "Zero age conversion failed"
    assert parser._convert_age_to_iso8601(365) == 'P365D', "Large age conversion failed"

    print("✅ Age conversion edge cases: PASS")

    # Test datetime combination edge cases
    assert parser._combine_datetime('', '14:30') == '', "Empty date should return empty"
    assert parser._combine_datetime('2024-01-15', '') == '', "Empty time should return empty"
    assert parser._combine_datetime('2024-01-15', '09:05') == '2024-01-15T09:05:00', \
        "Time with leading zeros failed"

    print("✅ Datetime combination edge cases: PASS")

    print("\n✅ ALL EDGE CASE TESTS PASSED\n")


def test_output_format():
    """Test that output format matches expected NWB structure."""
    print("=" * 60)
    print("Test 4: Output Format")
    print("=" * 60)

    parser = ELabFTWMetadataParser(
        api_key="mock_key",
        elabftw_url="https://mock.elabftw.com",
        verify_ssl=False
    )

    mock_metadata = create_mock_metadata()
    nwb_metadata = parser.map_to_nwb_metadata(mock_metadata)

    # Check top-level keys
    expected_keys = [
        'subject', 'indicator', 'viral_vector', 'fiber_insertion',
        'session', 'optical_fiber', 'excitation_source', 'photodetector',
        'dichroic_mirror', 'emission_filter', 'fiber_photometry_table',
        'provenance'
    ]

    for key in expected_keys:
        assert key in nwb_metadata, f"Missing top-level key: {key}"

    print("✅ Top-level structure: PASS")

    # Check that numeric fields are actually numeric
    assert isinstance(nwb_metadata['optical_fiber']['core_diameter_in_um'], float), \
        "Fiber diameter should be float"
    assert isinstance(nwb_metadata['indicator']['injection_coordinates_in_mm'], tuple), \
        "Injection coordinates should be tuple"
    assert len(nwb_metadata['indicator']['injection_coordinates_in_mm']) == 3, \
        "Injection coordinates should have 3 values"

    print("✅ Data types: PASS")

    # Print sample output
    print("\n📄 Sample output structure:")
    print(json.dumps({k: type(v).__name__ for k, v in nwb_metadata.items()}, indent=2))

    print("\n✅ ALL OUTPUT FORMAT TESTS PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("eLabFTW Metadata Parser - Test Suite")
    print("=" * 60 + "\n")

    try:
        test_field_extraction()
        test_validation()
        test_edge_cases()
        test_output_format()

        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe parser is ready to use with real eLabFTW data.")
        print("Next steps:")
        print("  1. Set ELABFTW_API_KEY and ELABFTW_URL environment variables")
        print("  2. Create an experiment using the fiber photometry template")
        print("  3. Run: python parse_elabftw_metadata.py <experiment_id>")
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
