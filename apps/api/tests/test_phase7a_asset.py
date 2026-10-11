from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_aapl_performance_not_null():
    """Test that AAPL returns valid non-null performance metrics."""
    response = client.get("/api/v1/market/asset/AAPL")
    assert response.status_code == 200
    data = response.json()

    # Check that performance metrics are not null
    assert data["performance"]["1W"] is not None
    assert data["performance"]["1M"] is not None
    assert data["performance"]["6M"] is not None
    assert data["performance"]["1Y"] is not None

    # Check that they are numbers (int or float)
    assert isinstance(data["performance"]["1W"], (int, float))
    assert isinstance(data["performance"]["1M"], (int, float))
    assert isinstance(data["performance"]["6M"], (int, float))
    assert isinstance(data["performance"]["1Y"], (int, float))

    print(f"AAPL Performance: 1W={data['performance']['1W']}, 1M={data['performance']['1M']}, 6M={data['performance']['6M']}, 1Y={data['performance']['1Y']}")

def test_reliance_performance_not_null():
    """Test that RELIANCE.NS returns valid non-null performance metrics."""
    response = client.get("/api/v1/market/asset/RELIANCE.NS")
    assert response.status_code == 200
    data = response.json()

    # Check that performance metrics are not null
    assert data["performance"]["1W"] is not None
    assert data["performance"]["1M"] is not None
    assert data["performance"]["6M"] is not None
    assert data["performance"]["1Y"] is not None

    # Check that they are numbers (int or float)
    assert isinstance(data["performance"]["1W"], (int, float))
    assert isinstance(data["performance"]["1M"], (int, float))
    assert isinstance(data["performance"]["6M"], (int, float))
    assert isinstance(data["performance"]["1Y"], (int, float))

    print(f"RELIANCE.NS Performance: 1W={data['performance']['1W']}, 1M={data['performance']['1M']}, 6M={data['performance']['6M']}, 1Y={data['performance']['1Y']}")

def test_response_schema():
    """Test that the response adheres to the expected schema."""
    # Test AAPL
    response = client.get("/api/v1/market/asset/AAPL")
    assert response.status_code == 200
    data = response.json()

    # Check required fields
    required_fields = ["symbol", "company_name", "current_price", "currency",
                      "day_change_pct", "market_cap", "pe_ratio", "dividend_yield",
                      "fifty_two_week_high", "fifty_two_week_low", "performance",
                      "analyst_consensus"]
    for field in required_fields:
        assert field in data

    # Check performance sub-fields
    performance_fields = ["1W", "1M", "6M", "1Y"]
    for field in performance_fields:
        assert field in data["performance"]

    # Check analyst_consensus sub-fields
    consensus_fields = ["consensus", "target_price", "total_analysts"]
    for field in consensus_fields:
        assert field in data["analyst_consensus"]

if __name__ == "__main__":
    test_aapl_performance_not_null()
    test_reliance_performance_not_null()
    test_response_schema()
    print("All tests passed!")