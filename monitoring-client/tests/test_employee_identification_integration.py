"""Integration tests for employee identification and first-time setup.

This test verifies that task 2 and its subtasks are properly integrated.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.config import store_employee_name, retrieve_employee_name, get_employee_config_path
from src.setup_dialog import prompt_for_employee_name


@pytest.fixture
def clean_config():
    """Fixture to ensure clean config state before and after tests."""
    config_path = get_employee_config_path()
    
    # Backup existing config if it exists
    backup_path = None
    if config_path.exists():
        backup_path = config_path.with_suffix('.bak')
        config_path.rename(backup_path)
    
    yield
    
    # Clean up test config
    if config_path.exists():
        config_path.unlink()
    
    # Restore backup if it existed
    if backup_path and backup_path.exists():
        backup_path.rename(config_path)


class TestEmployeeIdentificationIntegration:
    """Integration tests for employee identification workflow."""
    
    def test_first_time_setup_workflow(self, clean_config):
        """
        Test the complete first-time setup workflow:
        1. No employee name exists
        2. Dialog is shown to prompt for name
        3. Name is stored persistently
        4. Subsequent calls retrieve the stored name without showing dialog
        
        Validates: Requirements 1.1, 1.2
        """
        # Verify no name exists initially
        assert retrieve_employee_name() is None
        
        # Mock the dialog to simulate user input
        # We need to mock it so that it actually stores the name
        def mock_show_dialog():
            store_employee_name("Test Employee")
            return "Test Employee"
        
        with patch('src.setup_dialog.EmployeeSetupDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.show = mock_show_dialog
            mock_dialog_class.return_value = mock_dialog
            
            # First call should show dialog
            name1 = prompt_for_employee_name()
            assert name1 == "Test Employee"
            mock_dialog_class.assert_called_once()
        
        # Verify name was stored
        stored_name = retrieve_employee_name()
        assert stored_name == "Test Employee"
        
        # Second call should NOT show dialog, just return stored name
        name2 = prompt_for_employee_name()
        assert name2 == "Test Employee"
    
    def test_employee_name_persistence_across_sessions(self, clean_config):
        """
        Test that employee name persists across different "sessions".
        
        Validates: Requirements 1.2
        """
        # Store name in "first session"
        store_employee_name("Alice Johnson")
        
        # Simulate new session by retrieving name
        retrieved_name = retrieve_employee_name()
        assert retrieved_name == "Alice Johnson"
        
        # Verify it can be retrieved multiple times
        for _ in range(3):
            name = retrieve_employee_name()
            assert name == "Alice Johnson"
    
    def test_employee_name_used_as_identifier(self, clean_config):
        """
        Test that the stored employee name can be used as a unique identifier.
        
        Validates: Requirements 1.3, 1.4
        """
        # Store employee name
        employee_name = "Bob Smith"
        store_employee_name(employee_name)
        
        # Simulate multiple data payload constructions
        # Each should use the same employee name
        payloads = []
        for i in range(5):
            # In real implementation, this would be part of payload construction
            name = retrieve_employee_name()
            payload = {
                "employee_name": name,
                "sequence": i,
                "data": f"test_data_{i}"
            }
            payloads.append(payload)
        
        # Verify all payloads have the same employee name
        employee_names = [p["employee_name"] for p in payloads]
        assert all(name == "Bob Smith" for name in employee_names)
        assert len(set(employee_names)) == 1  # All names are identical
    
    def test_whitespace_handling_in_workflow(self, clean_config):
        """
        Test that whitespace is properly handled throughout the workflow.
        
        Validates: Requirements 1.1, 1.2
        """
        # Store name with extra whitespace
        store_employee_name("  Charlie Brown  ")
        
        # Retrieved name should be trimmed
        name = retrieve_employee_name()
        assert name == "Charlie Brown"
        assert name == name.strip()
        
        # Verify it works with prompt_for_employee_name
        retrieved_via_prompt = prompt_for_employee_name()
        assert retrieved_via_prompt == "Charlie Brown"
    
    def test_config_file_location_and_structure(self, clean_config):
        """
        Test that the configuration file is created in the correct location
        with the correct structure.
        
        Validates: Requirements 1.2
        """
        # Store employee name
        store_employee_name("David Wilson")
        
        # Verify config file exists
        config_path = get_employee_config_path()
        assert config_path.exists()
        assert config_path.is_file()
        
        # Verify it's in the correct directory structure
        assert "VibgyorSeek" in str(config_path)
        assert config_path.name == "employee_config.json"
        
        # Verify file content structure
        import json
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        assert "employee_name" in data
        assert data["employee_name"] == "David Wilson"
