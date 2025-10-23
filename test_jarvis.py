import pytest
import asyncio
from unittest.mock import Mock, patch
from command_processor import CommandProcessor

@pytest.fixture
def processor():
    """Create test processor."""
    mock_gui = Mock()
    mock_app_manager = Mock()
    mock_memory = Mock()
    mock_tts = Mock()
    mock_predictor = Mock()
    
    return CommandProcessor(
        mock_gui,
        mock_app_manager,
        mock_memory,
        mock_tts,
        mock_predictor
    )

@pytest.mark.asyncio
async def test_execute_command(processor):
    """Test command execution."""
    result = await processor.execute("what time is it")
    assert ":" in result  # Should contain time

@pytest.mark.asyncio
async def test_web_search(processor):
    """Test web search."""
    result = await processor.web_search("python programming")
    assert len(result) > 0