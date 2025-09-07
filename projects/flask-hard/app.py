from flask import Flask, request, jsonify
from app.log_processor import LogProcessor

app = Flask(__name__)

# Initialize the LogProcessor singleton
log_processor = LogProcessor()


@app.route('/logs', methods=['POST'])
def add_log():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    log_entry = request.get_json()

    # Basic validation of required fields
    required_fields = ['timestamp', 'level', 'message']
    for field in required_fields:
        if field not in log_entry:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Validate level
    allowed_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    if log_entry['level'].upper() not in allowed_levels:
        return jsonify({'error': f'Invalid log level: {log_entry["level"]}'}), 400

    # Enqueue the log for processing
    try:
        # Normalize level to uppercase
        log_entry['level'] = log_entry['level'].upper()
        log_processor.enqueue_log(log_entry)
    except Exception as e:
        return jsonify({'error': f'Failed to process log: {str(e)}'}), 500

    return jsonify({'status': 'Log processed successfully'}), 201


@app.route('/logs', methods=['GET'])
def get_logs():
    level = request.args.get('level')
    sort_order = request.args.get('sort', 'asc').lower()
    sort_asc = sort_order != 'desc'

    logs = log_processor.get_logs(level=level, sort_asc=sort_asc)
    return jsonify(logs), 200


@app.route('/metrics', methods=['GET'])
def get_metrics():
    metrics = log_processor.get_metrics()
    return jsonify(metrics), 200
