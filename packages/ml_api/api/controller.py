from flask import Blueprint, request, jsonify
from regression_model.predict import make_prediction
from regression_model import __version__ as _version
import os
from werkzeug.utils import secure_filename

from api.config import get_logger, UPLOAD_FOLDER
from api.validation import validate_inputs
from api import __version__ as api_version

_logger = get_logger(logger_name=__name__)

prediction_app = Blueprint('prediction_app', __name__)


@prediction_app.route('/health', methods=['GET'])
def health():
    if request.method == 'GET':
        _logger.info('Health status OK')
        return 'ok'


@prediction_app.route('/version', methods=['GET'])
def version():
    if request.method == 'GET':
        return jsonify({
            'model_version': _version,
            'api_version': api_version
        })


@prediction_app.route('/v1/predict/regression', methods=['POST'])
def predict():
    if request.method == 'POST':
        json_data = request.get_json()

        _logger.debug(f'Inputs: {json_data}')

        input_data, errors = validate_inputs(input_data=json_data)

        result = make_prediction(input_data=input_data)
        _logger.debug(f'Outputs: {result}')

        predictions = result.get('predictions').tolist()
        version = result.get('version')

        return jsonify({
            'predictions': predictions,
            'version': version,
            'errors': errors
        })