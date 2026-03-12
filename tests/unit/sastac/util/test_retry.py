import pytest
from sastac.util.retry import retry

def test_retry_success_first_try():
    def mock_func():
        return "success"
        
    result = retry(mock_func, 3, "Test action")
    assert result == "success"

def test_retry_success_after_failure():
    attempts = 0
    
    def mock_func():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Failed")
        return "success"
        
    result = retry(mock_func, 3, "Test action")
    assert result == "success"
    assert attempts == 2

def test_retry_failure():
    attempts = 0
    
    def mock_func():
        nonlocal attempts
        attempts += 1
        raise ValueError("Failed")
        
    with pytest.raises(ValueError, match="Failed"):
        retry(mock_func, 3, "Test action")
    assert attempts == 3

def test_retry_with_args():
    def mock_func(a, b, *, c):
        return a + b + c
        
    result = retry(mock_func, 2, "Test action", 1, 2, c=3)
    assert result == 6
