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

    # TODO(you): decide how the API answers when validation reports errors.
    #
    # Context: validate_inputs returns (rows_that_passed, errors). When some
    # rows fail, _filter_error_rows has already DROPPED them, so `input_data`
    # is shorter than what the client sent. The old code ignored `errors`
    # entirely and returned 200 with a short predictions array, so the client
    # could not tell which of its rows a prediction belonged to.
    #
    # Implement the behaviour you want here (roughly 5-8 lines). Options:
    #   a) strict  - any error => 400, predict nothing. Simple contract,
    #                client must send clean data.
    #   b) partial - predict on surviving rows, return 200 with both
    #                predictions and errors. Flexible, but the client needs
    #                row indices to realign results.
    #   c) all-bad - 400 only when every row failed, otherwise 200 + errors.
    #
    # Whatever you pick, make sure the client can always map a prediction
    # back to the row it came from.

    result = make_prediction(input_data=input_data)
    _logger.debug(f'Outputs: {result}')

    predictions = result.get('predictions').tolist()
    version = result.get('version')

    return jsonify({
        'predictions': predictions,
        'version': version,
        'errors': errors
    })
