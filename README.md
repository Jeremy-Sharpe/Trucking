# Email Processing Application

This application processes emails from your Gmail account and extracts structured data using Google's Generative AI.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up configuration:
   - Copy `config.template.py` to `config.py`
   - Edit `config.py` with your credentials:
     - Gmail account settings
     - Gmail App Password (see below)
     - Google AI API key

5. Enable Gmail IMAP:
   - Go to Gmail Settings > See all settings > Forwarding and POP/IMAP
   - Enable IMAP
   - Save Changes

6. Create Gmail App Password:
   - Go to your Google Account settings
   - Enable 2-Step Verification if not already enabled
   - Go to Security > App passwords
   - Generate a new app password for "Mail"
   - Use this password in your `config.py`

7. Get Google AI API Key:
   - Go to https://ai.google.dev/
   - Create a new project or select an existing one
   - Enable the Generative Language API
   - Create credentials (API key)
   - Copy the API key to your `config.py`

## Running the Application

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the Flask application:
   ```bash
   python app.py
   ```

3. Open your browser and go to:
   ```
   http://localhost:5000
   ```

## Features

- Process unread emails from your Gmail inbox
- Extract customizable fields using Google's Generative AI
- Download extracted data in JSON or CSV format
- Add/remove fields to extract through the web interface
- View extracted data in a formatted table

## Security Notes

- The `config.py` file contains sensitive information and is excluded from git
- Use environment variables in production
- Never commit API keys or passwords
- Keep your App Password secure

## Troubleshooting

1. IMAP Connection Issues:
   - Ensure IMAP is enabled in Gmail
   - Check that you're using an App Password if 2FA is enabled
   - Verify your network connection

2. API Key Issues:
   - Ensure your Google AI API key is valid
   - Check API quotas and limits
   - Verify the API is enabled for your project

3. Data Extraction Issues:
   - Check the email format
   - Verify the fields you're trying to extract
   - Look for error messages in the console 