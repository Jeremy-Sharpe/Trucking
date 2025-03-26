"""
Fixed version of the email processor that avoids name conflicts.
"""
import imaplib
import os
import json
from datetime import datetime, timedelta
import traceback

# Import email module with an alias to avoid name conflicts
import email as email_pkg
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import our other modules
from llm_processor import extract_data_with_llm
from config import EMAIL_USERNAME, LLM_API_KEY
from auth import get_credentials

# Define trucking-related keywords
TRUCKING_KEYWORDS = {
    'shipment', 'delivery', 'truck', 'freight', 'cargo', 'load', 'transport',
    'shipping', 'carrier', 'destination', 'origin', 'pickup', 'delivery',
    'route', 'dispatch', 'logistics', 'pallet', 'warehouse', 'dock',
    'tracking', 'id', 'eta', 'arrival', 'departure', 'weight', 'consignment'
}

def is_trucking_related(body_text):
    """
    Check if the email is related to trucking by looking for relevant keywords.
    Returns True if at least one keyword is found, False otherwise.
    """
    if not body_text:
        return False
    
    # Convert email body to lowercase for case-insensitive matching
    body_lower = body_text.lower()
    
    # Count how many keywords are found
    found_keywords = [word for word in TRUCKING_KEYWORDS if word in body_lower]
    
    # Return True if at least one keyword is found
    if found_keywords:
        print(f"Found trucking-related keywords: {', '.join(found_keywords)}")
        return True
    else:
        print("No trucking-related keywords found in email")
        return False

def process_emails():
    """Process unread emails and extract relevant information."""
    try:
        print("Attempting to connect to email server...")
        
        # Get OAuth2 credentials
        credentials = get_credentials()
        if not credentials:
            print("No valid credentials found. Please log in first.")
            return []
            
        print(f"Got credentials with token length: {len(credentials.token)}")
        print(f"Token expired: {credentials.expired}")
        if hasattr(credentials, 'expiry'):
            print(f"Token valid until: {credentials.expiry}")
            
        # Create IMAP connection with retry logic
        max_retries = 3
        retry_count = 0
        mail = None
        
        while retry_count < max_retries:
            try:
                # Create IMAP connection
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                
                # Authenticate using OAuth2
                auth_string = f'user={EMAIL_USERNAME}\1auth=Bearer {credentials.token}\1\1'
                print(f"Using email: {EMAIL_USERNAME}")
                print(f"Auth string length: {len(auth_string)}")
                print(f"Token starts with: {credentials.token[:10]}...")
                
                # Debug IMAP connection
                print("IMAP connection established, attempting authentication...")
                mail.authenticate('XOAUTH2', lambda x: auth_string.encode())
                
                print("Successfully connected to email server")
                break  # If successful, break the retry loop
                
            except imaplib.IMAP4.error as e:
                retry_count += 1
                print(f"Authentication attempt {retry_count} failed: {str(e)}")
                
                if retry_count == max_retries:
                    print("Max retries reached. Please log in again.")
                    return []
                    
                # Try to refresh credentials before retrying
                print("Attempting to refresh credentials...")
                credentials = get_credentials()
                if not credentials:
                    print("Failed to refresh credentials")
                    return []
                    
                print("Retrying with refreshed credentials...")
                continue
                
        # Select the inbox
        mail.select('INBOX')
        
        # Get date 24 hours ago in the required format (DD-MMM-YYYY)
        date_since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        print(f"Searching for emails since: {date_since}")
        
        # Try multiple search approaches for compatibility
        found_emails = False
        message_numbers = None
        search_criteria = ""
        
        # Approach 1: Try standard UNSEEN SINCE search
        try:
            print("Trying standard UNSEEN SINCE search...")
            search_criteria = f'(UNSEEN SINCE "{date_since}")'
            print(f"Using search criteria: {search_criteria}")
            _, message_numbers = mail.search(None, search_criteria)
            if message_numbers and message_numbers[0]:
                found_emails = True
                print(f"Found {len(message_numbers[0].split())} unread emails since {date_since}")
        except Exception as e:
            print(f"Standard search failed: {e}")
        
        # Approach 2: If no emails found, try just UNSEEN
        if not found_emails:
            try:
                print("Trying simple UNSEEN search...")
                search_criteria = 'UNSEEN'
                _, message_numbers = mail.search(None, search_criteria)
                if message_numbers and message_numbers[0]:
                    found_emails = True
                    print(f"Found {len(message_numbers[0].split())} unread emails")
            except Exception as e:
                print(f"UNSEEN search failed: {e}")
        
        # Approach 3: Last resort, try ALL and filter later
        if not found_emails:
            try:
                print("Trying to search for ALL emails as last resort...")
                search_criteria = 'ALL'
                _, message_numbers = mail.search(None, search_criteria)
                if message_numbers and message_numbers[0]:
                    found_emails = True
                    print(f"Found {len(message_numbers[0].split())} total emails, will filter later")
            except Exception as e:
                print(f"ALL search failed: {e}")
                return []  # If we can't even search, exit
        
        if not message_numbers or not message_numbers[0]:
            print("No emails found with any search method")
            return []
        
        email_ids = message_numbers[0].split()
        print(f"Processing {len(email_ids)} emails")
        
        # Limit to processing at most 10 emails to avoid overload
        if len(email_ids) > 10:
            print(f"Limiting to processing 10 emails out of {len(email_ids)} found")
            email_ids = email_ids[:10]
        
        extracted_data = []
        email_utils = email_pkg.utils  # Use alias to avoid conflicts
        
        # Process each email
        for msg_id in email_ids:
            try:
                # Fetch the email message
                _, msg_data = mail.fetch(msg_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email_pkg.message_from_bytes(raw_email)
                
                # Get email metadata
                msg_date = msg['date']
                msg_subject = msg['subject'] or ""
                msg_from = msg['from'] or ""
                
                # Check if the email is unread (if we used ALL search)
                if search_criteria == 'ALL':
                    # Look for \Seen flag
                    _, flags_data = mail.fetch(msg_id, '(FLAGS)')
                    if '\\Seen' in str(flags_data[0]):
                        print(f"Skipping read email: {msg_subject}")
                        continue
                
                # Check date if necessary (if we didn't use SINCE in search)
                if 'SINCE' not in search_criteria:
                    # Parse the email date
                    try:
                        date_tuple = email_utils.parsedate_tz(msg_date)
                        if date_tuple:
                            parsed_datetime = datetime.fromtimestamp(email_utils.mktime_tz(date_tuple))
                            cutoff_date = datetime.now() - timedelta(days=1)
                            if parsed_datetime < cutoff_date:
                                print(f"Skipping old email from {parsed_datetime}: {msg_subject}")
                                continue
                    except Exception as e:
                        print(f"Error parsing date, processing anyway: {e}")
                
                print(f"Processing email: {msg_subject} from {msg_from} dated {msg_date}")
                
                # Get email content
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode()
                                break
                            except Exception:
                                body = part.get_payload(decode=True).decode('latin-1', errors='ignore')
                                break
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except Exception:
                        body = msg.get_payload(decode=True).decode('latin-1', errors='ignore')
                
                # Check if email is trucking-related
                if not is_trucking_related(body):
                    print(f"Skipping non-trucking email: {msg_subject}")
                    continue
                
                # Extract data using LLM
                fields_to_extract = ['shipment_id', 'origin', 'destination', 'pickup_date', 'delivery_date', 'carrier', 'status']
                extracted_info = extract_data_with_llm(body, fields_to_extract)
                
                if extracted_info:
                    # Add email metadata
                    extracted_info['email_subject'] = msg_subject
                    extracted_info['email_date'] = msg_date
                    extracted_info['email_from'] = msg_from
                    extracted_data.append(extracted_info)
                    print(f"Successfully processed email: {msg_subject}")
                else:
                    print(f"No valid data found in email: {msg_subject}")
                
            except Exception as e:
                print(f"Error processing email {msg_id}: {str(e)}")
                print(traceback.format_exc())
                continue
        
        # Close the connection
        mail.close()
        mail.logout()
        
        return extracted_data
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(traceback.format_exc())
        return []

def save_to_json(data, filename='extracted_data.json'):
    """Save extracted data to a JSON file."""
    try:
        # Load existing data if file exists
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing_data = json.load(f)
        
        # Append new data
        existing_data.extend(data)
        
        # Save updated data
        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=2)
            
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {str(e)}")

if __name__ == "__main__":
    # Test the email processing
    extracted_data = process_emails()
    if extracted_data:
        save_to_json(extracted_data) 