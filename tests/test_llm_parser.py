import pytest
from llm_parser import LLMParser


def test_duration_extraction():
    """Test duration extraction from text"""
    parser = LLMParser()
    
    assert parser._extract_duration("2 hours") == 120.0
    assert parser._extract_duration("30 minutes") == 30.0
    assert parser._extract_duration("45m") == 45.0
    assert parser._extract_duration("1.5h") == 90.0
    assert parser._extract_duration("no duration") is None


def test_parse_natural_language_mock():
    """Test natural language parsing (mock test without API call)"""
    parser = LLMParser()
    
    # Test duration extraction part
    text = "I spent 2 hours coding"
    duration = parser._extract_duration(text)
    assert duration == 120.0

