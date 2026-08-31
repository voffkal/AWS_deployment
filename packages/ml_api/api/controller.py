from flask import Blueprint, request, jsonify
from regression_model.predict import make_prediction
from regression_model import __version__ as _version

from api.config import get_logger
from api.validation import validate_inputs
from api import __version__ as api_version

_logger = get_logger(logger_name=__name__)

prediction_app = Blueprint('prediction_app', __name__)


@prediction_app.route('/health', methods=['GET'])
def health():
    _logger.info('Health status OK')
    return 'ok'


@prediction_app.route('/version', methods=['GET'])
def version():
    return jsonify({
        'model_version': _version,
        'api_version': api_version
    })


@prediction_app.route('/v1/predict/regression', methods=['POST'])
def predict():
    json_data = request.get_json()

    if not json_data:
        return jsonify({'errors': 'No input data provided'}), 400

    _logger.debug(f'Inputs: {json_data}')

    input_data, errors = validate_inputs(input_data=json_data)

    # Invalid rows are a client problem: refuse the batch instead of
    # answering 200 with fewer predictions than rows submitted.
    if errors is not None:
        _logger.warning(f'Input validation failed: {errors}')
        return jsonify({'errors': errors}), 400

    result = make_prediction(input_data=input_data)
    _logger.debug(f'Outputs: {result}')

    predictions = result.get('predictions').tolist()
    version = result.get('version')

    return jsonify({
        'predictions': predictions,
        'version': version,
        'errors': errors
    })
