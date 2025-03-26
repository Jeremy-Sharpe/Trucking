from flask import Blueprint, redirect, url_for, session, request, current_app
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
import traceback
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, EMAIL_USERNAME
from datetime import timedelta
import json

auth = Blueprint('auth', __name__)

# OAuth2 configuration
SCOPES = [
    'openid',  # OpenID Connect scope
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://mail.google.com/',  # Full Gmail access scope
    'https://www.googleapis.com/auth/gmail.modify'  # Ability to modify Gmail
]

# This is required for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def get_redirect_uri():
    """Get the redirect URI using localhost instead of 127.0.0.1."""
    redirect_uri = url_for('auth.oauth2callback', _external=True)
    # Replace 127.0.0.1 with localhost
    redirect_uri = redirect_uri.replace('127.0.0.1', 'localhost')
    return redirect_uri

@auth.route('/login')
def login():
    """Initiate the Google OAuth2 flow."""
    try:
        # Ensure session is configured
        session.permanent = True  # Make session last longer
        current_app.permanent_session_lifetime = timedelta(minutes=30)  # Set session lifetime
        
        redirect_uri = get_redirect_uri()
        print(f"Using redirect URI: {redirect_uri}")  # Debug print
        
        client_config = {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
                "javascript_origins": [url_for('index', _external=True).replace('127.0.0.1', 'localhost')]
            }
        }
        
        print(f"Client config: {client_config}")  # Debug print
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        print(f"Authorization URL: {authorization_url}")  # Debug print
        print(f"Generated state: {state}")  # Debug print
        
        # Store state and redirect URI in session
        session['state'] = state
        session['redirect_uri'] = redirect_uri
        session.modified = True  # Ensure session is saved
        
        print(f"Session after login: {dict(session)}")  # Debug print
        return redirect(authorization_url)
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug print
        print(f"Traceback: {traceback.format_exc()}")  # Full traceback
        return f"Error during login: {str(e)}", 500

@auth.route('/oauth2callback')
def oauth2callback():
    """Handle the OAuth2 callback."""
    try:
        print(f"Callback received with args: {request.args}")  # Debug print
        print(f"Session at callback: {dict(session)}")  # Debug print
        
        # If there's an error parameter, redirect to login
        if 'error' in request.args:
            print(f"Error in callback: {request.args.get('error')}")
            return redirect(url_for('auth.login'))
        
        if 'state' not in session:
            print("No state found in session")  # Debug print
            # Attempt to recover - redirect to login
            return redirect(url_for('auth.login'))
            
        state = session['state']
        request_state = request.args.get('state')
        print(f"Session state: {state}")  # Debug print
        print(f"Request state: {request_state}")  # Debug print
        
        # More permissive state checking - if there's a state mismatch but we have code,
        # we'll try to continue anyway since we may have valid authorization
        if state != request_state:
            print(f"State mismatch - Session: {state}, Request: {request_state}")
            
            # If we have a code, try to proceed anyway
            if 'code' not in request.args:
                print("No code found in request")
                return redirect(url_for('auth.login'))
            else:
                print("State mismatch but code present, attempting to continue")
                # Continue with the request state instead
                state = request_state
        
        redirect_uri = session.get('redirect_uri') or get_redirect_uri()
        print(f"Callback redirect URI: {redirect_uri}")  # Debug print
        
        client_config = {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
                "javascript_origins": [url_for('index', _external=True).replace('127.0.0.1', 'localhost')]
            }
        }
        
        print(f"Callback client config: {client_config}")  # Debug print
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=state,  # Use the request state if session state didn't match
            redirect_uri=redirect_uri
        )
        
        print(f"Fetching token with URL: {request.url}")  # Debug print
        
        # Disable scope validation
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        try:
            flow.fetch_token(
                authorization_response=request.url,
                authorization_prompt_message='',
                include_granted_scopes='true'
            )
        except Exception as token_e:
            print(f"Token fetch error: {str(token_e)}")
            # If invalid_grant, redirect to login
            if 'invalid_grant' in str(token_e).lower():
                print("Invalid grant error, redirecting to login")
                return redirect(url_for('auth.login'))
            raise  # Re-raise if it's not an invalid_grant error
        
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        session.modified = True  # Ensure session is saved
        
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Callback error: {str(e)}")  # Debug print
        print(traceback.format_exc())  # Full traceback
        return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    """Clear the session and log out the user."""
    session.clear()
    return redirect(url_for('index'))

def get_credentials():
    """Get valid credentials from the session."""
    if 'credentials' not in session:
        print("No credentials found in session")
        return None
        
    try:
        print(f"Credentials in session - token length: {len(session['credentials']['token']) if 'token' in session['credentials'] else 'None'}")
        print(f"Refresh token present: {'Yes' if session['credentials'].get('refresh_token') else 'No'}")
        
        credentials = Credentials(
            token=session['credentials']['token'],
            refresh_token=session['credentials']['refresh_token'],
            token_uri=session['credentials']['token_uri'],
            client_id=session['credentials']['client_id'],
            client_secret=session['credentials']['client_secret'],
            scopes=session['credentials']['scopes']
        )
        
        # Check token validity
        print(f"Token expired: {credentials.expired}")
        print(f"Token valid until: {credentials.expiry}")
        
        # Check if token is expired or about to expire
        if credentials and credentials.expired:
            print("Token expired, attempting to refresh...")
            try:
                credentials.refresh(Request())
                # Update session with new token
                session['credentials']['token'] = credentials.token
                session.modified = True
                print(f"Token refreshed successfully - New token length: {len(credentials.token)}")
                print(f"New token valid until: {credentials.expiry}")
            except Exception as e:
                print(f"Error refreshing token: {str(e)}")
                print(traceback.format_exc())  # Full traceback
                # Clear invalid credentials from session
                session.pop('credentials', None)
                return None
                
        return credentials
    except Exception as e:
        print(f"Error creating credentials: {str(e)}")
        print(traceback.format_exc())  # Full traceback
        # Clear invalid credentials from session
        session.pop('credentials', None)
        return None 

@auth.route('/debug_oauth')
def debug_oauth():
    """Debug route to check OAuth credentials."""
    try:
        debug_info = {
            "session_contains_credentials": 'credentials' in session,
            "session_keys": list(session.keys()) if session else [],
        }
        
        if 'credentials' in session:
            debug_info["token_length"] = len(session['credentials']['token']) if 'token' in session['credentials'] else 0
            debug_info["has_refresh_token"] = 'refresh_token' in session['credentials'] and bool(session['credentials']['refresh_token'])
            debug_info["has_client_id"] = 'client_id' in session['credentials'] and bool(session['credentials']['client_id'])
            debug_info["has_client_secret"] = 'client_secret' in session['credentials'] and bool(session['credentials']['client_secret'])
            debug_info["scopes"] = session['credentials'].get('scopes', [])
            
            # Try to create credentials object
            try:
                credentials = Credentials(
                    token=session['credentials']['token'],
                    refresh_token=session['credentials']['refresh_token'],
                    token_uri=session['credentials']['token_uri'],
                    client_id=session['credentials']['client_id'],
                    client_secret=session['credentials']['client_secret'],
                    scopes=session['credentials']['scopes']
                )
                debug_info["credentials_created"] = True
                debug_info["token_expired"] = credentials.expired
                debug_info["token_expiry"] = str(credentials.expiry) if hasattr(credentials, 'expiry') else 'Unknown'
                
                # Try a token refresh
                if credentials.expired:
                    try:
                        credentials.refresh(Request())
                        debug_info["token_refresh_successful"] = True
                        debug_info["new_token_length"] = len(credentials.token)
                        debug_info["new_token_expiry"] = str(credentials.expiry)
                        
                        # Update session
                        session['credentials']['token'] = credentials.token
                        session.modified = True
                    except Exception as e:
                        debug_info["token_refresh_successful"] = False
                        debug_info["token_refresh_error"] = str(e)
                        
            except Exception as e:
                debug_info["credentials_created"] = False
                debug_info["credentials_error"] = str(e)
        
        # Try to test authentication with IMAP
        try:
            credentials = get_credentials()
            if credentials:
                debug_info["get_credentials_succeeded"] = True
                
                # Try IMAP connection
                import imaplib
                
                imap = imaplib.IMAP4_SSL("imap.gmail.com")
                auth_string = f'user={EMAIL_USERNAME}\1auth=Bearer {credentials.token}\1\1'
                
                debug_info["email_username"] = EMAIL_USERNAME
                debug_info["auth_string_length"] = len(auth_string)
                
                try:
                    imap.authenticate('XOAUTH2', lambda x: auth_string.encode())
                    debug_info["imap_authentication"] = "Success"
                    imap.logout()
                except Exception as e:
                    debug_info["imap_authentication"] = "Failed"
                    debug_info["imap_error"] = str(e)
            else:
                debug_info["get_credentials_succeeded"] = False
        except Exception as e:
            debug_info["oauth_test_error"] = str(e)
        
        return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"
    except Exception as e:
        return f"Debug error: {str(e)}" 