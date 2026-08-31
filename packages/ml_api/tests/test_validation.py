import json

from regression_model.config import config
from regression_model.processing.data_management import load_dataset


def test_prediction_endpoint_validation_200(flask_test_client):
    # Given
    # Load the test data from the regression_model package.
    # This is important as it makes it harder for the test
    # data versions to get confused by not spreading it
    # across packages.
    test_data = load_dataset(file_name=config.TESTING_DATA_FILE)
    post_json = test_data.to_json(orient='records')

    # When
    response = flask_test_client.post('/v1/predict/regression',
                                      json=json.loads(post_json))

    # Then
    # NOTE: this test pins the CURRENT contract - invalid rows are dropped and
    # the endpoint still answers 200. If you implement the strict variant of
    # the TODO in api/controller.py (any error => 400), update this test to
    # expect 400 instead; a failure here means the contract changed.
    assert response.status_code == 200
    response_json = json.loads(response.data)

    # Every input row is accounted for: either predicted or reported as an error.
    assert len(response_json.get('predictions')) + len(
        response_json.get('errors')) == len(test_data)