"""Property-based tests for the payload builder module.

Feature: vibgyorseek-employee-monitoring
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock
from datetime import datetime, timezone
from src.payload_builder import PayloadBuilder
from src.activity_tracker import ActivityState


# Strategies for generating test data
employee_name_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nd', 'Pc', 'Pd', 'Zs'),
        min_codepoint=32,
        max_codepoint=126
    ),
    min_size=1,
    max_size=100
).filter(lambda s: s.strip())  # Ensure at least one non-whitespace character


# Strategy for generating activity data (work_seconds, idle_seconds)
activity_data_strategy = st.tuples(
    st.integers(min_value=0, max_value=3600),  # work_seconds
    st.integers(min_value=0, max_value=3600),  # idle_seconds
    st.sampled_from([ActivityState.WORK, ActivityState.IDLE])  # current_state
)


# Strategy for generating application lists
application_strategy = st.lists(
    st.fixed_dictionaries({
        'name': st.text(min_size=1, max_size=50),
        'active': st.booleans()
    }),
    min_size=0,
    max_size=20
)


# Strategy for generating browser tab lists
browser_tab_strategy = st.lists(
    st.fixed_dictionaries({
        'browser': st.sampled_from(['Chrome', 'Firefox', 'Edge']),
        'title': st.text(min_size=1, max_size=100),
        'url': st.text(min_size=1, max_size=200)
    }),
    min_size=0,
    max_size=50
)


# Strategy for generating screenshot data (base64 string or None)
screenshot_strategy = st.one_of(
    st.none(),
    st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48, max_codepoint=122), min_size=10, max_size=100)
)


def create_mock_payload_builder(activity_data, applications, browser_tabs, screenshot):
    """Helper function to create a PayloadBuilder with mocked dependencies."""
    # Mock activity tracker
    mock_activity_tracker = Mock()
    mock_activity_tracker.get_activity_data.return_value = activity_data
    
    # Mock application monitor
    mock_app_monitor = Mock()
    mock_app_monitor.get_running_applications.return_value = applications
    
    # Mock browser monitor
    mock_browser_monitor = Mock()
    mock_browser_monitor.get_browser_tabs.return_value = browser_tabs
    
    # Mock screenshot capture
    mock_screenshot_capture = Mock()
    mock_screenshot_capture.capture_screenshot.return_value = screenshot
    
    return PayloadBuilder(
        activity_tracker=mock_activity_tracker,
        app_monitor=mock_app_monitor,
        browser_monitor=mock_browser_monitor,
        screenshot_capture=mock_screenshot_capture
    )


class TestPayloadStructureProperties:
    """Property-based tests for payload structure.
    
    **Validates: Requirements 1.3, 1.4, 2.5, 3.4, 4.3, 5.4, 6.5**
    """
    
    @given(
        employee_name=employee_name_strategy,
        activity_data=activity_data_strategy,
        applications=application_strategy,
        browser_tabs=browser_tab_strategy,
        screenshot=screenshot_strategy
    )
    @settings(max_examples=100)
    def test_property_data_payload_completeness(
        self,
        employee_name,
        activity_data,
        applications,
        browser_tabs,
        screenshot
    ):
        """
        Property 2: Data Payload Completeness
        
        For any data payload sent by the Monitoring_Client, it must contain 
        all required fields: employee_name, timestamp, interval_start, 
        interval_end, activity (with work_seconds and idle_seconds), 
        applications list, browser_tabs list, and screenshot data.
        
        **Validates: Requirements 1.3, 2.5, 3.4, 4.3, 5.4, 6.5**
        """
        # Create payload builder with mocked dependencies
        payload_builder = create_mock_payload_builder(
            activity_data, applications, browser_tabs, screenshot
        )
        
        # Build the payload
        payload = payload_builder.build_payload("test-client-id", employee_name)
        
        # Property: All required top-level fields must be present
        required_fields = [
            'employee_name',
            'timestamp',
            'interval_start',
            'interval_end',
            'activity',
            'applications',
            'browser_tabs',
            'screenshot'
        ]
        
        for field in required_fields:
            assert field in payload, f"Required field '{field}' missing from payload"
        
        # Property: Activity field must contain work_seconds and idle_seconds
        assert 'work_seconds' in payload['activity'], \
            "Required field 'work_seconds' missing from activity"
        assert 'idle_seconds' in payload['activity'], \
            "Required field 'idle_seconds' missing from activity"
        
        # Property: employee_name must be a non-empty string
        assert isinstance(payload['employee_name'], str), \
            "employee_name must be a string"
        assert len(payload['employee_name'].strip()) > 0, \
            "employee_name must not be empty"
        
        # Property: Timestamps must be valid ISO format strings
        for ts_field in ['timestamp', 'interval_start', 'interval_end']:
            assert isinstance(payload[ts_field], str), \
                f"{ts_field} must be a string"
            # Verify it can be parsed as ISO format
            try:
                datetime.fromisoformat(payload[ts_field])
            except ValueError:
                pytest.fail(f"{ts_field} is not a valid ISO format timestamp")
        
        # Property: Activity data must be integers
        assert isinstance(payload['activity']['work_seconds'], int), \
            "work_seconds must be an integer"
        assert isinstance(payload['activity']['idle_seconds'], int), \
            "idle_seconds must be an integer"
        
        # Property: Applications must be a list
        assert isinstance(payload['applications'], list), \
            "applications must be a list"
        
        # Property: Browser tabs must be a list
        assert isinstance(payload['browser_tabs'], list), \
            "browser_tabs must be a list"
        
        # Property: Screenshot must be a string (empty string if None)
        assert isinstance(payload['screenshot'], str), \
            "screenshot must be a string"
    
    @given(
        employee_name=employee_name_strategy,
        activity_data=activity_data_strategy,
        applications=application_strategy,
        browser_tabs=browser_tab_strategy,
        screenshot=screenshot_strategy,
        num_transmissions=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100)
    def test_property_employee_identifier_consistency(
        self,
        employee_name,
        activity_data,
        applications,
        browser_tabs,
        screenshot,
        num_transmissions
    ):
        """
        Property 3: Employee Identifier Consistency
        
        For any sequence of data transmissions from the same Monitoring_Client 
        instance, the employee_name field should remain constant across all payloads.
        
        **Validates: Requirements 1.4**
        """
        # Create payload builder with mocked dependencies
        payload_builder = create_mock_payload_builder(
            activity_data, applications, browser_tabs, screenshot
        )
        
        # Build multiple payloads from the same client instance
        payloads = []
        for _ in range(num_transmissions):
            payload = payload_builder.build_payload("test-client-id", employee_name)
            payloads.append(payload)
        
        # Property: All payloads should have the same employee_name
        expected_name = employee_name.strip()
        for i, payload in enumerate(payloads):
            assert payload['employee_name'] == expected_name, \
                f"Payload {i+1} has inconsistent employee_name: " \
                f"expected '{expected_name}', got '{payload['employee_name']}'"
        
        # Property: All employee names should be identical across transmissions
        employee_names = [p['employee_name'] for p in payloads]
        assert len(set(employee_names)) == 1, \
            f"Employee names are not consistent across transmissions: {employee_names}"
