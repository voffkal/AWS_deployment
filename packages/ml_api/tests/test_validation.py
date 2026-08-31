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
    # The contract is strict: if any row carries a null in a feature the model
    # actually uses, the whole batch is refused. The shipped Kaggle test set
    # contains 8 such rows (nulls in MSZoning / KitchenQual / BsmtFullBath /
    # GarageCars, none of which the pipeline imputes).
    assert response.status_code == 400
    response_json = json.loads(response.data)

    # The response names every offending row, so the caller can fix and resend.
    errors = response_json['errors']
    assert errors
    offending_fields = {f for row in errors.values() for f in row}
    assert offending_fields <= {
        'MSZoning', 'KitchenQual', 'BsmtFullBath', 'GarageCars'
    }


def test_prediction_endpoint_accepts_legitimate_nulls(flask_test_client):
    # Given
    # In the Ames data "NA" means "no garage" / "no basement" - a value, not a
    # gap. Those fields are not model features, so they must not fail a request.
    test_data = load_dataset(file_name=config.TESTING_DATA_FILE)
    clean = test_data.dropna(
        subset=['MSZoning', 'KitchenQual', 'BsmtFullBath', 'GarageCars']
    )
    post_json = clean.to_json(orient='records')

    # When
    response = flask_test_client.post('/v1/predict/regression',
                                      json=json.loads(post_json))

    # Then
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json['errors'] is None
    assert len(response_json['predictions']) == len(clean)