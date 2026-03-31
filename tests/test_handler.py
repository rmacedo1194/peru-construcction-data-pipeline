import os

from app.lambda_app.handler import lambda_handler


def test_lambda_handler():
    os.environ["API_BASE_URL"] = "https://example.com/api"
    os.environ["RAW_BUCKET_NAME"] = "demo-raw-bucket"
    os.environ["SOURCE_NAME"] = "peru_construction"
    os.environ["REQUEST_TIMEOUT"] = "30"

    event = {
        "dataset": "peru_construction_licenses"
    }

    response = lambda_handler(event, None)

    assert response["status"] == "success"
    assert response["dataset"] == "peru_construction_licenses"
    assert "demo-raw-bucket" in response["message"]
