"""Property-based tests for configuration module.

Feature: vibgyorseek-employee-monitoring
"""

import os
import tempfile
import unittest.mock as mock
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
from src.config import Config, store_employee_name, retrieve_employee_name


# Strategy for generating valid employee names
# Valid names should be non-empty strings with at least one non-whitespace character
employee_name_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nd', 'Pc', 'Pd', 'Zs'),
        min_codepoint=32,
        max_codepoint=126
    ),
    min_size=1,
    max_size=100
).filter(lambda s: s.strip())  # Ensure at least one non-whitespace character


# Strategy for generating valid configuration values
config_values_strategy = st.fixed_dictionaries({
    'server_url': st.just('https://test.com'),  # Required field
    'auth_token': st.just('test-token'),  # Required field
    'screenshot_interval_minutes': st.one_of(st.none(), st.integers(min_value=1, max_value=1440)),
    'data_send_interval_minutes': st.one_of(st.none(), st.integers(min_value=1, max_value=1440)),
    'idle_threshold_seconds': st.one_of(st.none(), st.integers(min_value=1, max_value=3600)),
    'screenshot_quality': st.one_of(st.none(), st.integers(min_value=1, max_value=100)),
    'log_level': st.one_of(st.none(), st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']))
})


class TestEmployeeNamePersistenceProperty:
    """Property-based tests for employee name persistence.
    
    **Validates: Requirements 1.2**
    """
    
    @given(name=employee_name_strategy)
    @settings(max_examples=20)
    def test_employee_name_persistence_property(self, name):
        """
        Property 1: Employee Name Persistence
        
        For any valid employee name, storing the name in the client configuration
        and then retrieving it should return the same name.
        
        **Validates: Requirements 1.2**
        """
        # Create a temporary directory for this test iteration
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Mock the config path to use tmp_path with a unique file per iteration
            def mock_get_path():
                return tmp_path / f'employee_config_{abs(hash(name))}.json'
            
            with mock.patch('src.config.get_employee_config_path', mock_get_path):
                # Store the employee name
                store_employee_name(name)
                
                # Retrieve the employee name
                retrieved_name = retrieve_employee_name()
                
                # Property: Retrieved name should equal the stored name (after stripping)
                # The implementation strips whitespace, so we compare with stripped version
                assert retrieved_name == name.strip()



class TestConfigurationRoundTripProperty:
    """Property-based tests for configuration round-trip.
    
    **Validates: Requirements 6.1, 8.1, 8.5, 8.6**
    """
    
    @given(config_values=config_values_strategy)
    @settings(max_examples=100)
    def test_configuration_round_trip_property(self, config_values):
        """
        Property 9: Configuration Round-Trip
        
        For any valid configuration file with defined parameters, loading the
        configuration should return all specified parameter values, and missing
        parameters should return documented default values.
        
        **Validates: Requirements 6.1, 8.1, 8.5, 8.6**
        """
        # Save current environment variables
        env_vars = [
            'SERVER_URL', 'AUTH_TOKEN', 'SCREENSHOT_INTERVAL_MINUTES',
            'DATA_SEND_INTERVAL_MINUTES', 'IDLE_THRESHOLD_SECONDS',
            'SCREENSHOT_QUALITY', 'LOG_LEVEL'
        ]
        saved_env = {var: os.environ.get(var) for var in env_vars}
        
        try:
            # Clear all environment variables that might interfere
            for var in env_vars:
                if var in os.environ:
                    del os.environ[var]
            
            # Create a temporary directory for this test iteration
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                env_file = tmp_path / '.env'
                
                # Build .env file content with only non-None values
                env_content = []
                env_content.append(f"SERVER_URL={config_values['server_url']}")
                env_content.append(f"AUTH_TOKEN={config_values['auth_token']}")
                
                if config_values['screenshot_interval_minutes'] is not None:
                    env_content.append(f"SCREENSHOT_INTERVAL_MINUTES={config_values['screenshot_interval_minutes']}")
                
                if config_values['data_send_interval_minutes'] is not None:
                    env_content.append(f"DATA_SEND_INTERVAL_MINUTES={config_values['data_send_interval_minutes']}")
                
                if config_values['idle_threshold_seconds'] is not None:
                    env_content.append(f"IDLE_THRESHOLD_SECONDS={config_values['idle_threshold_seconds']}")
                
                if config_values['screenshot_quality'] is not None:
                    env_content.append(f"SCREENSHOT_QUALITY={config_values['screenshot_quality']}")
                
                if config_values['log_level'] is not None:
                    env_content.append(f"LOG_LEVEL={config_values['log_level']}")
                
                env_file.write_text('\n'.join(env_content))
                
                # Load configuration
                config = Config(str(env_file))
                
                # Property: All specified values should be returned correctly
                assert config.server_url == config_values['server_url']
                assert config.auth_token == config_values['auth_token']
                
                # Property: Missing values should return documented defaults
                if config_values['screenshot_interval_minutes'] is not None:
                    assert config.screenshot_interval_minutes == config_values['screenshot_interval_minutes']
                else:
                    assert config.screenshot_interval_minutes == Config.DEFAULT_SCREENSHOT_INTERVAL_MINUTES
                
                if config_values['data_send_interval_minutes'] is not None:
                    assert config.data_send_interval_minutes == config_values['data_send_interval_minutes']
                else:
                    assert config.data_send_interval_minutes == Config.DEFAULT_DATA_SEND_INTERVAL_MINUTES
                
                if config_values['idle_threshold_seconds'] is not None:
                    assert config.idle_threshold_seconds == config_values['idle_threshold_seconds']
                else:
                    assert config.idle_threshold_seconds == Config.DEFAULT_IDLE_THRESHOLD_SECONDS
                
                if config_values['screenshot_quality'] is not None:
                    assert config.screenshot_quality == config_values['screenshot_quality']
                else:
                    assert config.screenshot_quality == Config.DEFAULT_SCREENSHOT_QUALITY
                
                if config_values['log_level'] is not None:
                    assert config.log_level == config_values['log_level']
                else:
                    assert config.log_level == Config.DEFAULT_LOG_LEVEL
        finally:
            # Restore original environment variables
            for var, value in saved_env.items():
                if value is not None:
                    os.environ[var] = value
                elif var in os.environ:
                    del os.environ[var]
