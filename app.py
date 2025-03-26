from flask import Flask, render_template, send_file, request, jsonify, session, redirect, url_for
import io
import json
import csv
from email_processor import process_emails
from llm_processor import extract_data_with_llm
from auth import auth, get_credentials
from config import SECRET_KEY

app = Flask(__name__)
app.register_blueprint(auth)
app.secret_key = SECRET_KEY

# Default fields to extract
default_fields = ['shipment_id', 'origin', 'destination', 'departure_date', 'arrival_date']
current_fields = default_fields.copy()
latest_data = []

def login_required(f):
    """Decorator to require login for routes."""
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    if 'credentials' not in session:
        return render_template('login.html')
        
    global latest_data, current_fields
    email_bodies = process_emails()
    # Filter out None values from the results
    latest_data = [result for result in (extract_data_with_llm(body, current_fields) for body in email_bodies if body) if result is not None]
    return render_template('index.html', data=latest_data, fields=current_fields)

@app.route('/update_fields', methods=['POST'])
@login_required
def update_fields():
    global current_fields
    data = request.get_json()
    if 'fields' in data:
        current_fields = data['fields']
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'No fields provided'}), 400

@app.route('/download/json')
@login_required
def download_json():
    global latest_data
    if not latest_data:
        return "No data available", 404
    
    # Convert the data to JSON string and encode to bytes
    json_str = json.dumps(latest_data, indent=2)
    json_bytes = json_str.encode('utf-8')
    
    # Create a BytesIO object and write the bytes to it
    output = io.BytesIO(json_bytes)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/json',
        as_attachment=True,
        download_name='data.json'
    )

@app.route('/download/csv')
@login_required
def download_csv():
    global latest_data, current_fields
    if not latest_data:
        return "No data available", 404
        
    flat_data = []
    for item in latest_data:
        flat_item = {}
        for key in current_fields:
            subdict = item.get(key, {})
            flat_item[f"{key}_value"] = subdict.get('value', '')
            flat_item[f"{key}_context"] = subdict.get('context', '')
        flat_data.append(flat_item)
    
    # Create a string buffer and write CSV data to it
    string_buffer = io.StringIO()
    writer = csv.DictWriter(string_buffer, fieldnames=[f"{key}_{suffix}" for key in current_fields for suffix in ['value', 'context']])
    writer.writeheader()
    writer.writerows(flat_data)
    
    # Convert to bytes and create BytesIO object
    csv_bytes = string_buffer.getvalue().encode('utf-8')
    bytes_buffer = io.BytesIO(csv_bytes)
    bytes_buffer.seek(0)
    
    return send_file(
        bytes_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='data.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)