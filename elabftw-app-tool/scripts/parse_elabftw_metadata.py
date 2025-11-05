#!/usr/bin/env python3
"""
eLabFTW Metadata Parser for ndx-fiber-photometry NWB Files

This script extracts metadata from eLabFTW experiment entries and maps it to
the ndx-fiber-photometry NWB extension format.

Author: elabftw-app
Created: 2025-11-03
License: MIT
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import elabapi_python
from elabapi_python.rest import ApiException


class ELabFTWMetadataParser:
    """
    Parser for eLabFTW fiber photometry experiment metadata.

    Maps eLabFTW extra_fields to ndx-fiber-photometry NWB metadata structure.
    """

    def __init__(
        self,
        api_key: str,
        elabftw_url: str,
        verify_ssl: bool = True,
        debug: bool = False
    ):
        """
        Initialize the parser with eLabFTW API credentials.

        Args:
            api_key: eLabFTW API key
            elabftw_url: Base URL of eLabFTW instance (e.g., https://elabftw.example.com)
            verify_ssl: Whether to verify SSL certificates (default: True)
            debug: Enable debug logging (default: False)
        """
        self.api_key = api_key
        self.elabftw_url = elabftw_url
        self.verify_ssl = verify_ssl
        self.debug = debug

        # Configure API client
        self.configuration = elabapi_python.Configuration()
        self.configuration.api_key['api_key'] = api_key
        self.configuration.api_key_prefix['api_key'] = 'Authorization'
        self.configuration.host = f"{elabftw_url}/api/v2"
        self.configuration.debug = debug
        self.configuration.verify_ssl = verify_ssl

        # Create API client and experiments API
        self.api_client = elabapi_python.ApiClient(self.configuration)
        self.experiments_api = elabapi_python.ExperimentsApi(self.api_client)

    def get_experiment_metadata(self, experiment_id: int) -> Dict[str, Any]:
        """
        Fetch experiment metadata from eLabFTW.

        Args:
            experiment_id: eLabFTW experiment ID

        Returns:
            Dictionary containing experiment data including metadata

        Raises:
            ApiException: If API call fails
        """
        try:
            experiment = self.experiments_api.read_experiment(id=experiment_id)
            return {
                'id': experiment.id,
                'title': experiment.title,
                'body': experiment.body,
                'metadata': experiment.metadata,
                'created_at': experiment.created_at,
                'modified_at': experiment.modified_at
            }
        except ApiException as e:
            raise ApiException(f"Failed to fetch experiment {experiment_id}: {e}")

    def _get_field_value(self, fields: Dict[str, Any], field_name: str, default: Any = '') -> Any:
        """
        Extract value from eLabFTW extra_fields.

        Args:
            fields: extra_fields dictionary
            field_name: Name of the field to extract
            default: Default value if field doesn't exist or is empty

        Returns:
            Field value or default
        """
        field_data = fields.get(field_name, {})
        value = field_data.get('value', default)

        # Return default if value is None or empty string
        if value is None or value == '':
            return default

        return value

    def _convert_age_to_iso8601(self, age_days: Optional[int]) -> Optional[str]:
        """
        Convert age in days to ISO 8601 duration format.

        Args:
            age_days: Age in days (integer or None)

        Returns:
            ISO 8601 duration string (e.g., "P90D") or None
        """
        if age_days is None or age_days == '':
            return None

        try:
            days = int(age_days)
            return f"P{days}D"
        except (ValueError, TypeError):
            return None

    def _combine_datetime(self, date_str: str, time_str: str) -> str:
        """
        Combine date and time strings into ISO 8601 timestamp.

        Args:
            date_str: Date string (YYYY-MM-DD)
            time_str: Time string (HH:MM)

        Returns:
            ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SS)
        """
        if not date_str or not time_str:
            return ''

        try:
            # Ensure time has seconds
            if len(time_str.split(':')) == 2:
                time_str = f"{time_str}:00"

            return f"{date_str}T{time_str}"
        except Exception:
            return ''

    def validate_required_fields(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Validate that all required fields are present and non-empty.

        Args:
            metadata: Metadata dictionary with 'extra_fields'

        Returns:
            List of error messages (empty list if all valid)
        """
        errors = []
        fields = metadata.get('extra_fields', {})

        # Required fields for NWB file generation
        required_fields = [
            'Subject ID',
            'Species',
            'Sex',
            'Surgery Date',
            'Indicator Label',
            'Injection Location',
            'Injection AP (mm)',
            'Injection ML (mm)',
            'Injection DV (mm)',
            'Session ID',
            'Session Date',
            'Session Time',
            'Experimenter',
            'Fiber Core Diameter (μm)',
            'Fiber Numerical Aperture',
            'Excitation Wavelength (nm)',
            'Emission Wavelength (nm)',
            'Recording Location'
        ]

        for field in required_fields:
            value = self._get_field_value(fields, field, None)
            if value is None or value == '':
                errors.append(f"Required field missing or empty: {field}")

        return errors

    def validate_data_ranges(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Validate that numeric fields are within reasonable ranges.

        Args:
            metadata: Metadata dictionary with 'extra_fields'

        Returns:
            List of warning messages
        """
        warnings = []
        fields = metadata.get('extra_fields', {})

        # Validate stereotactic coordinates (mm)
        coordinate_fields = {
            'Injection AP (mm)': (-10, 10),
            'Injection ML (mm)': (-10, 10),
            'Injection DV (mm)': (0, 15),
            'Fiber Implant Depth (mm)': (0, 15)
        }

        for field_name, (min_val, max_val) in coordinate_fields.items():
            value = self._get_field_value(fields, field_name, None)
            if value and value != '':
                try:
                    val = float(value)
                    if val < min_val or val > max_val:
                        warnings.append(
                            f"{field_name} value {val} outside typical range "
                            f"({min_val} to {max_val} mm)"
                        )
                except (ValueError, TypeError):
                    warnings.append(f"{field_name} is not a valid number: {value}")

        # Validate wavelengths (nm)
        wavelength_fields = {
            'Excitation Wavelength (nm)': (300, 800),
            'Emission Wavelength (nm)': (400, 900),
            'Dichroic Mirror Cut-on (nm)': (300, 800),
            'Emission Filter Center (nm)': (400, 900)
        }

        for field_name, (min_val, max_val) in wavelength_fields.items():
            value = self._get_field_value(fields, field_name, None)
            if value and value != '':
                try:
                    val = float(value)
                    if val < min_val or val > max_val:
                        warnings.append(
                            f"{field_name} value {val} outside typical range "
                            f"({min_val} to {max_val} nm)"
                        )
                except (ValueError, TypeError):
                    warnings.append(f"{field_name} is not a valid number: {value}")

        # Validate numerical aperture
        na_value = self._get_field_value(fields, 'Fiber Numerical Aperture', None)
        if na_value and na_value != '':
            try:
                na = float(na_value)
                if na < 0.1 or na > 1.0:
                    warnings.append(
                        f"Fiber Numerical Aperture {na} outside typical range (0.1 to 1.0)"
                    )
            except (ValueError, TypeError):
                warnings.append(f"Fiber Numerical Aperture is not a valid number: {na_value}")

        return warnings

    def map_to_nwb_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map eLabFTW metadata to ndx-fiber-photometry NWB structure.

        Args:
            metadata: eLabFTW metadata dictionary with 'extra_fields'

        Returns:
            Dictionary with NWB-ready metadata grouped by object type
        """
        fields = metadata.get('extra_fields', {})

        # Group 1: Subject metadata (NWB Subject object)
        subject_metadata = {
            'subject_id': self._get_field_value(fields, 'Subject ID'),
            'species': self._get_field_value(fields, 'Species', 'Mus musculus'),
            'sex': self._get_field_value(fields, 'Sex'),
            'age': self._convert_age_to_iso8601(
                self._get_field_value(fields, 'Age (days)', None)
            ),
            'strain': self._get_field_value(fields, 'Strain', None),
            'genotype': self._get_field_value(fields, 'Genotype', None),
            'weight': self._get_field_value(fields, 'Weight (grams)', None)
        }

        # Group 2: Indicator metadata
        injection_location = self._get_field_value(fields, 'Injection Location')
        indicator_label = self._get_field_value(fields, 'Indicator Label')

        indicator_metadata = {
            'name': f"{indicator_label}_{injection_location}",
            'label': indicator_label,
            'injection_location': injection_location,
            'injection_coordinates_in_mm': (
                float(self._get_field_value(fields, 'Injection AP (mm)', 0)),
                float(self._get_field_value(fields, 'Injection ML (mm)', 0)),
                float(self._get_field_value(fields, 'Injection DV (mm)', 0))
            ),
            'description': f"{indicator_label} injected in {injection_location}"
        }

        # Group 2b: Viral vector metadata
        viral_vector_metadata = {
            'name': self._get_field_value(fields, 'Viral Vector Name', None),
            'titer': self._get_field_value(fields, 'Viral Titer', None),
            'injection_volume_nl': self._get_field_value(fields, 'Injection Volume (nL)', None)
        }

        # Group 2c: Fiber insertion metadata
        fiber_insertion_metadata = {
            'depth_mm': self._get_field_value(fields, 'Fiber Implant Depth (mm)', None),
            'location': injection_location
        }

        # Group 3: Session metadata (NWB file-level metadata)
        session_date = self._get_field_value(fields, 'Session Date')
        session_time = self._get_field_value(fields, 'Session Time')

        session_metadata = {
            'session_id': self._get_field_value(fields, 'Session ID'),
            'session_start_time': self._combine_datetime(session_date, session_time),
            'session_description': self._get_field_value(
                fields, 'Session Description', 'Fiber photometry recording session'
            ),
            'experimenter': [self._get_field_value(fields, 'Experimenter')],
            'lab': self._get_field_value(fields, 'Laboratory', None),
            'institution': self._get_field_value(fields, 'Institution', 'NIH NIMH')
        }

        # Group 4: Device metadata
        fiber_diameter = self._get_field_value(fields, 'Fiber Core Diameter (μm)', 400)

        optical_fiber_metadata = {
            'name': f"Fiber_{fiber_diameter}um",
            'model': self._get_field_value(fields, 'Optical Fiber Model', None),
            'numerical_aperture': float(
                self._get_field_value(fields, 'Fiber Numerical Aperture', 0)
            ),
            'core_diameter_in_um': float(fiber_diameter)
        }

        excitation_wavelength = self._get_field_value(fields, 'Excitation Wavelength (nm)', 470)

        excitation_source_metadata = {
            'name': f"LED_{excitation_wavelength}nm",
            'excitation_wavelength_in_nm': float(excitation_wavelength),
            'power_mw': self._get_field_value(fields, 'LED Power (mW)', None)
        }

        emission_wavelength = self._get_field_value(fields, 'Emission Wavelength (nm)', 520)

        photodetector_metadata = {
            'name': f"PMT_{emission_wavelength}nm",
            'detected_wavelength_in_nm': float(emission_wavelength),
            'gain': self._get_field_value(fields, 'PMT Gain', None)
        }

        # Optional: Dichroic mirror
        dichroic_cutoff = self._get_field_value(fields, 'Dichroic Mirror Cut-on (nm)', None)
        dichroic_mirror_metadata = None
        if dichroic_cutoff:
            dichroic_mirror_metadata = {
                'name': f"Dichroic_{dichroic_cutoff}nm",
                'cut_on_wavelength_in_nm': float(dichroic_cutoff)
            }

        # Optional: Emission filter
        filter_center = self._get_field_value(fields, 'Emission Filter Center (nm)', None)
        emission_filter_metadata = None
        if filter_center:
            emission_filter_metadata = {
                'name': f"Filter_{filter_center}nm",
                'center_wavelength_in_nm': float(filter_center),
                'bandwidth_in_nm': self._get_field_value(
                    fields, 'Emission Filter Bandwidth (nm)', None
                )
            }

        # Group 5: FiberPhotometryTable metadata
        recording_location = self._get_field_value(fields, 'Recording Location')

        fiber_photometry_table_metadata = {
            'location': recording_location,
            'excitation_wavelength_in_nm': float(excitation_wavelength),
            'emission_wavelength_in_nm': float(emission_wavelength),
            'channel_name': self._get_field_value(
                fields, 'Channel Name', f"{indicator_label}_{excitation_wavelength}nm"
            ),
            'sampling_rate_hz': self._get_field_value(fields, 'Sampling Rate (Hz)', None)
        }

        # Group 6: Additional provenance metadata
        provenance_metadata = {
            'surgery_date': self._get_field_value(fields, 'Surgery Date'),
            'protocol_name': self._get_field_value(fields, 'Protocol Name', None),
            'data_file_path': self._get_field_value(fields, 'Data File Path', None),
            'behavioral_task': self._get_field_value(fields, 'Behavioral Task', None),
            'drug_treatment': self._get_field_value(fields, 'Drug Treatment', None),
            'notes': self._get_field_value(fields, 'Notes', None),
            'analysis_status': self._get_field_value(fields, 'Analysis Status', 'Pending'),
            'quality_control': self._get_field_value(fields, 'Quality Control', None)
        }

        return {
            'subject': subject_metadata,
            'indicator': indicator_metadata,
            'viral_vector': viral_vector_metadata,
            'fiber_insertion': fiber_insertion_metadata,
            'session': session_metadata,
            'optical_fiber': optical_fiber_metadata,
            'excitation_source': excitation_source_metadata,
            'photodetector': photodetector_metadata,
            'dichroic_mirror': dichroic_mirror_metadata,
            'emission_filter': emission_filter_metadata,
            'fiber_photometry_table': fiber_photometry_table_metadata,
            'provenance': provenance_metadata
        }

    def parse_experiment(
        self,
        experiment_id: int,
        validate: bool = True
    ) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Parse eLabFTW experiment and return NWB-ready metadata.

        Args:
            experiment_id: eLabFTW experiment ID
            validate: Whether to run validation (default: True)

        Returns:
            Tuple of (nwb_metadata, errors, warnings)
                - nwb_metadata: Dictionary with NWB-formatted metadata
                - errors: List of validation errors
                - warnings: List of validation warnings
        """
        # Fetch experiment data
        experiment_data = self.get_experiment_metadata(experiment_id)
        metadata = experiment_data.get('metadata', {})

        errors = []
        warnings = []

        # Validate if requested
        if validate:
            errors = self.validate_required_fields(metadata)
            warnings = self.validate_data_ranges(metadata)

        # Map to NWB format
        nwb_metadata = self.map_to_nwb_metadata(metadata)

        # Add experiment-level metadata
        nwb_metadata['elabftw'] = {
            'experiment_id': experiment_data.get('id'),
            'title': experiment_data.get('title'),
            'created_at': experiment_data.get('created_at'),
            'modified_at': experiment_data.get('modified_at')
        }

        return nwb_metadata, errors, warnings


def main():
    """
    CLI interface for the parser.

    Usage:
        python parse_elabftw_metadata.py <experiment_id>

    Environment variables:
        ELABFTW_API_KEY: eLabFTW API key (required)
        ELABFTW_URL: eLabFTW instance URL (required)
        ELABFTW_VERIFY_SSL: Verify SSL certificates (default: true)
    """
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python parse_elabftw_metadata.py <experiment_id>")
        print("\nEnvironment variables required:")
        print("  ELABFTW_API_KEY - Your eLabFTW API key")
        print("  ELABFTW_URL - Your eLabFTW instance URL")
        print("  ELABFTW_VERIFY_SSL - Verify SSL (default: true)")
        sys.exit(1)

    experiment_id = int(sys.argv[1])

    # Get configuration from environment
    api_key = os.environ.get('ELABFTW_API_KEY')
    elabftw_url = os.environ.get('ELABFTW_URL')
    verify_ssl = os.environ.get('ELABFTW_VERIFY_SSL', 'true').lower() == 'true'

    if not api_key:
        print("Error: ELABFTW_API_KEY environment variable not set")
        sys.exit(1)

    if not elabftw_url:
        print("Error: ELABFTW_URL environment variable not set")
        sys.exit(1)

    # Initialize parser
    parser = ELabFTWMetadataParser(
        api_key=api_key,
        elabftw_url=elabftw_url,
        verify_ssl=verify_ssl,
        debug=False
    )

    try:
        # Parse experiment
        print(f"Fetching experiment {experiment_id} from {elabftw_url}...")
        nwb_metadata, errors, warnings = parser.parse_experiment(experiment_id)

        # Display results
        if errors:
            print("\n❌ ERRORS:")
            for error in errors:
                print(f"  - {error}")
            print("\nCannot generate NWB file with validation errors.")
            sys.exit(1)

        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  - {warning}")

        print("\n✅ Validation passed!")
        print(f"\nParsed metadata for experiment: {nwb_metadata['elabftw']['title']}")
        print(f"Subject: {nwb_metadata['subject']['subject_id']}")
        print(f"Session: {nwb_metadata['session']['session_id']}")
        print(f"Indicator: {nwb_metadata['indicator']['label']} @ {nwb_metadata['indicator']['injection_location']}")

        # Save to JSON file
        output_file = f"experiment_{experiment_id}_nwb_metadata.json"
        with open(output_file, 'w') as f:
            json.dump(nwb_metadata, f, indent=2, default=str)

        print(f"\n📄 Metadata saved to: {output_file}")

    except ApiException as e:
        print(f"\n❌ API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
