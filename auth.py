from flask import Blueprint, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY

auth = Blueprint('auth', __name__)

# OAuth2 configuration
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly'
]

# This is required for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

@auth.route('/login')
def login():
    """Initiate the Google OAuth2 flow."""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [url_for('auth.oauth2callback', _external=True)],
                "scopes": SCOPES
            }
        }
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)

@auth.route('/oauth2callback')
def oauth2callback():
    """Handle the OAuth2 callback."""
    state = session['state']
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [url_for('auth.oauth2callback', _external=True)],
                "scopes": SCOPES
            }
        },
        state=state
    )
    
    flow.fetch_token(
        authorization_response=request.url,
        authorization_prompt_message='',
        include_granted_scopes='true'
    )
    
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return redirect(url_for('index'))

@auth.route('/logout')
def logout():
    """Clear the session and log out the user."""
    session.clear()
    return redirect(url_for('index'))

def get_credentials():
    """Get valid credentials from the session."""
    if 'credentials' not in session:
        return None
        
    credentials = Credentials(
        token=session['credentials']['token'],
        refresh_token=session['credentials']['refresh_token'],
        token_uri=session['credentials']['token_uri'],
        client_id=session['credentials']['client_id'],
        client_secret=session['credentials']['client_secret'],
        scopes=session['credentials']['scopes']
    )
    
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        session['credentials']['token'] = credentials.token
        
    return credentials 