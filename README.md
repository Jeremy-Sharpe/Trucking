# Trucking Email Processor

A web application that uses Gmail's API and Google's Generative AI to automatically extract structured data from trucking-related emails.

## Features

- **Google OAuth2 Authentication**: Securely connect to your Gmail account using Google's OAuth2 protocol
- **Smart Email Filtering**: Only processes unread emails from the past 24 hours that contain trucking-related keywords
- **Customizable Data Extraction**: Add, remove, or modify which fields to extract from your emails
- **Advanced AI Processing**: Uses Google's Generative AI to analyze email content and extract relevant logistics data
- **Export Options**: Download extracted data in JSON or CSV format
- **Mobile-Friendly UI**: Modern, responsive user interface that works on all devices

## Setup

### Prerequisites

- Python 3.8 or higher
- A Google Cloud Project with Gmail API enabled
- Google OAuth2 credentials (client ID and secret)
- Google Generative AI API key

### Configuration

1. Clone this repository:
```bash
git clone https://github.com/yourusername/trucking-email-processor.git
cd trucking-email-processor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `config.py` file based on the template:
```python
# Google OAuth credentials
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-client-secret"

# Email settings
EMAIL_USERNAME = "your-email@gmail.com"

# LLM settings
LLM_API_KEY = "your-google-ai-api-key"

# Flask settings
SECRET_KEY = "your-secret-key"  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
```

### Setting up Google Cloud OAuth

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project
4. Create OAuth 2.0 credentials (Web application type)
5. Add the following authorized redirect URI:
   - `http://localhost:5000/oauth2callback`
6. Add the following authorized JavaScript origin:
   - `http://localhost:5000`

### Running the Application

1. Start the Flask application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Sign in with your Google account
4. Customize the fields you want to extract
5. Click "Update and Process Emails" to extract data from trucking-related emails

## Usage

### Authentication

The application uses Google OAuth2 to securely access your Gmail account. On your first visit, you'll need to:

1. Click "Sign in with Google"
2. Grant permission to access your Gmail account
3. You'll be redirected back to the application

### Customizing Fields

1. Add new fields by entering their names in the "Enter new field name" input and clicking "Add Field"
2. Remove fields by clicking the "Remove" button next to any field
3. Click "Update and Process Emails" to apply your changes and process emails

### Processing Emails

The application will:
1. Search for unread emails from the past 24 hours in your Gmail inbox
2. Filter for trucking-related emails based on keywords (e.g., shipment, delivery, freight)
3. Extract data for the specified fields using Google's Generative AI
4. Display the extracted data in a table format
5. Save the data for future reference

### Downloading Data

1. Click "Download JSON" to download the structured data in JSON format
2. Click "Download CSV" to download the data as a CSV file for use in spreadsheets

## Technical Details

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Authentication**: Google OAuth2
- **Email Access**: Gmail API with IMAP
- **Data Extraction**: Google's Generative AI (Gemini model)
- **Session Management**: Flask-Session with filesystem storage

## Security Features

- OAuth2 token handling with automatic refresh
- Session encryption
- Secure cookie handling
- No storage of Gmail credentials
- Config file excluded from version control

## License

[MIT License](LICENSE) 