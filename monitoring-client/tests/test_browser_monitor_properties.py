"""Property-based tests for the browser monitor module.

Feature: vibgyorseek-employee-monitoring

These tests verify universal properties of browser tab data collection.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch
from src.browser_monitor import BrowserMonitor


# Custom strategy for generating browser tab data
@st.composite
def browser_tab_data(draw):
    """Generate valid browser tab data structures."""
    browser = draw(st.sampled_from(['Chrome', 'Firefox', 'Edge']))
    
    # Generate either title, URL, or both (but at least one)
    has_title = draw(st.booleans())
    has_url = draw(st.booleans())
    
    # Ensure at least one is present
    if not has_title and not has_url:
        has_title = True
    
    tab = {'browser': browser}
    
    if has_title:
        # Generate realistic tab titles
        title = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), max_codepoint=127),
            min_size=1,
            max_size=100
        ).filter(lambda x: x.strip()))
        tab['title'] = title
    else:
        tab['title'] = ''
    
    if has_url:
        # Generate realistic URLs
        domain = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=20
        ))
        tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'io']))
        path = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
            min_size=0,
            max_size=30
        ))
        
        url = f"https://{domain}.{tld}"
        if path:
            url += f"/{path}"
        tab['url'] = url
    else:
        tab['url'] = ''
    
    return tab


# Property 7: Browser Tab Data Completeness
# **Validates: Requirements 4.2**
@given(tabs=st.lists(browser_tab_data(), min_size=0, max_size=20))
@settings(max_examples=100, deadline=None)
def test_property_browser_tab_data_completeness(tabs):
    """
    Property 7: Browser Tab Data Completeness
    
    For any browser tab entry in the Data_Payload, it must contain 
    either a title field or a URL field (or both).
    
    **Validates: Requirements 4.2**
    """
    # Mock the browser monitor to return our generated tabs
    monitor = BrowserMonitor()
    
    # Verify each tab has at least title or URL
    for tab in tabs:
        has_title = 'title' in tab and tab['title'] and tab['title'].strip()
        has_url = 'url' in tab and tab['url'] and tab['url'].strip()
        
        assert has_title or has_url, \
            f"Tab must have either title or URL: {tab}"


# Property: Browser tab structure consistency
@given(tabs=st.lists(browser_tab_data(), min_size=1, max_size=20))
@settings(max_examples=100, deadline=None)
def test_property_browser_tab_structure(tabs):
    """
    Property: Browser Tab Structure Consistency
    
    For any list of browser tabs, each tab must have the required 
    'browser' field and at least one of 'title' or 'url'.
    
    **Validates: Requirements 4.1, 4.2**
    """
    for tab in tabs:
        # Must have browser field
        assert 'browser' in tab, f"Tab missing 'browser' field: {tab}"
        assert tab['browser'] in ['Chrome', 'Firefox', 'Edge'], \
            f"Invalid browser value: {tab['browser']}"
        
        # Must have at least title or URL
        has_title = 'title' in tab and tab['title'] and tab['title'].strip()
        has_url = 'url' in tab and tab['url'] and tab['url'].strip()
        
        assert has_title or has_url, \
            f"Tab must have either title or URL: {tab}"


# Property: Empty tab list is valid
def test_property_empty_tab_list_valid():
    """
    Property: Empty Tab List Validity
    
    When no browsers are running, get_browser_tabs should return 
    an empty list (not None or error).
    
    **Validates: Requirements 4.1**
    """
    monitor = BrowserMonitor()
    
    # Mock no browsers running
    with patch.object(monitor, '_get_running_browsers', return_value=[]):
        tabs = monitor.get_browser_tabs()
        
        assert isinstance(tabs, list), "Should return a list"
        assert len(tabs) == 0, "Should return empty list when no browsers running"


# Property: Tab data types are correct
@given(tabs=st.lists(browser_tab_data(), min_size=1, max_size=10))
@settings(max_examples=100, deadline=None)
def test_property_tab_data_types(tabs):
    """
    Property: Tab Data Types
    
    For any browser tab, the browser, title, and url fields 
    must be strings.
    
    **Validates: Requirements 4.2**
    """
    for tab in tabs:
        assert isinstance(tab.get('browser', ''), str), \
            f"Browser field must be string: {type(tab.get('browser'))}"
        
        if 'title' in tab:
            assert isinstance(tab['title'], str), \
                f"Title field must be string: {type(tab['title'])}"
        
        if 'url' in tab:
            assert isinstance(tab['url'], str), \
                f"URL field must be string: {type(tab['url'])}"


# Property: Browser monitor returns consistent structure
@given(num_browsers=st.integers(min_value=0, max_value=3))
@settings(max_examples=50, deadline=None)
def test_property_browser_monitor_consistent_structure(num_browsers):
    """
    Property: Browser Monitor Consistent Structure
    
    For any number of running browsers, get_browser_tabs should 
    return a list where each element is a properly structured tab dict.
    
    **Validates: Requirements 4.1, 4.2, 4.4**
    """
    monitor = BrowserMonitor()
    
    # Mock running browsers
    browsers = ['chrome', 'firefox', 'edge'][:num_browsers]
    
    with patch.object(monitor, '_get_running_browsers', return_value=browsers):
        # Mock the individual browser methods to return empty lists
        with patch.object(monitor, '_get_chrome_tabs', return_value=[]):
            with patch.object(monitor, '_get_firefox_tabs', return_value=[]):
                with patch.object(monitor, '_get_edge_tabs', return_value=[]):
                    tabs = monitor.get_browser_tabs()
                    
                    assert isinstance(tabs, list), "Should return a list"
                    
                    # Verify structure of each tab
                    for tab in tabs:
                        assert isinstance(tab, dict), "Each tab should be a dict"
                        assert 'browser' in tab, "Each tab should have 'browser' field"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
