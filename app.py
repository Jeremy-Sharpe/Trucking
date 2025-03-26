from flask import Flask, render_template, send_file, request, jsonify, session, redirect, url_for
import io
import json
import csv
from email_processor import process_emails, save_to_json
from llm_processor import extract_data_with_llm
from auth import auth, get_credentials
from config import SECRET_KEY
from flask_session import Session
from datetime import timedelta
import os

app = Flask(__name__)

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['SESSION_FILE_MODE'] = 0o600

# Initialize Flask-Session
Session(app)

app.register_blueprint(auth)

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
    return render_template('index.html', data=latest_data, fields=current_fields)

@app.route('/update_fields', methods=['POST'])
@login_required
def update_fields():
    global current_fields
    data = request.get_json()
    if 'fields' in data:
        # Update the fields to extract
        current_fields = data['fields']
        return jsonify({'status': 'success', 'message': 'Fields updated successfully'})
    return jsonify({'status': 'error', 'message': 'No fields provided'}), 400

@app.route('/download/json')
@login_required
def download_json():
    global latest_data
    if not latest_data:
        return "No data available", 404
    
    # Convert the data to JSON string and encode to bytes
    # Filter out entries where all values are "N/A"
    filtered_data = []
    for item in latest_data:
        # Check if all values are N/A
        all_na = True
        for field in current_fields:
            if field in item and 'value' in item[field] and item[field]['value'] != 'N/A':
                all_na = False
                break
        
        # Only include items that have at least one non-N/A value
        if not all_na:
            filtered_data.append(item)
    
    json_str = json.dumps(filtered_data, indent=2)
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
        
    # Filter out entries where all values are "N/A"
    filtered_data = []
    for item in latest_data:
        # Check if all values are N/A
        all_na = True
        for field in current_fields:
            if field in item and 'value' in item[field] and item[field]['value'] != 'N/A':
                all_na = False
                break
        
        # Only include items that have at least one non-N/A value
        if not all_na:
            filtered_data.append(item)
    
    flat_data = []
    for item in filtered_data:
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

@app.route('/process_emails', methods=['POST'])
def process_emails_endpoint():
    """Process emails and return results."""
    try:
        global latest_data, current_fields
        
        if 'credentials' not in session:
            return jsonify({"error": "Not authenticated. Please sign in first."}), 401
            
        # Process emails with the current fields
        results = process_emails(fields_to_extract=current_fields)
        
        if not results:
            return jsonify({"message": "No relevant emails found or processing failed. Check server logs for details."})
            
        # Update the latest_data with these results
        latest_data = results
        
        # Save results to JSON file
        save_to_json(results)
        
        return jsonify({
            "success": True,
            "message": f"Successfully processed {len(results)} emails",
            "data": results
        })
    except Exception as e:
        print(f"Error in process_emails endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)