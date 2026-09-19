"""
Test Cases for Counter Web Service

Create a service that can keep a track of multiple counters
- API must be RESTful - see the status.py file. Following these guidelines, you can make assumptions about
how to call the web service and assert what it should return.
- The endpoint should be called /counters
- When creating a counter, you must specify the name in the path.
- Duplicate names must return a conflict error code.
- The service must be able to update a counter by name.
- The service must be able to read the counter
"""
import pytest
from src import app
from src import status
from src.counter import COUNTERS
@pytest.fixture()
def client():
    """Fixture for Flask test client"""
    return app.test_client()

@pytest.mark.usefixtures("client")
class TestCounterEndpoints:
    """Test cases for Counter API"""

    def test_create_counter(self, client):
        """It should create a counter"""
        result = client.post('/counters/foo')
        assert result.status_code == status.HTTP_201_CREATED    
    
    def test_delete_counter(self, client):
        """It should delete an existing counter"""
        # Create a counter first
        client.post('/counters/foo')
        assert 'foo' in COUNTERS

        # Delete it
        result = client.delete('/counters/foo')
        assert result.status_code == status.HTTP_204_NO_CONTENT

        # Confirm it's actually gone
        assert 'foo' not in COUNTERS
    
    def test_get_existing_counter(self, client):
        """It should retrieve an existing counter"""
        client.post('/counters/omari')

        result = client.get('/counters/omari')

        assert result.status_code == status.HTTP_200_OK
        assert result.get_json() == {"omari": 0}

    def test_increment_counter(self, client):
        """It should increment an existing counter"""
        client.post('/counters/apple')

        result = client.put('/counters/apple')

        assert result.status_code == status.HTTP_200_OK
        assert result.get_json() == {"apple": 1}

    def test_get_nonexistent_counter(self, client):
        """It should return 404 when retrieving a non-existent counter"""
        result = client.get('/counters/nonexistent')

        assert result.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_counter_names(self, client):
        """It should reject invalid counter names"""
        # Invalid names
        invalid_names = [" ", "   ", "counter with spaces", "cou$nter!"]
        for name in invalid_names:
            result = client.post(f'/counters/{name}')
            assert result.status_code == status.HTTP_400_BAD_REQUEST
            assert result.get_json() == {
                "error": "Counter name must contain only letters and numbers"
            }

        # Test valid names
        valid_names = ["123", "abcd", "COUNTER3"]
        for name in valid_names:
            result = client.post(f'/counters/{name}')
            assert result.status_code == status.HTTP_201_CREATED
            assert result.get_json() == {name: 0}
