import imaplib
import email
from datetime import datetime, timedelta
from auth import get_credentials

# Define trucking-related keywords
TRUCKING_KEYWORDS = {
    'shipment', 'delivery', 'truck', 'freight', 'cargo', 'load', 'transport',
    'shipping', 'carrier', 'destination', 'origin', 'pickup', 'delivery',
    'route', 'dispatch', 'logistics', 'pallet', 'warehouse', 'dock',
    'tracking', 'id', 'eta', 'arrival', 'departure', 'weight', 'consignment'
}

def is_trucking_related(email_body):
    """
    Check if the email is related to trucking by looking for relevant keywords.
    Returns True if at least one keyword is found, False otherwise.
    """
    if not email_body:
        return False
    
    # Convert email body to lowercase for case-insensitive matching
    email_lower = email_body.lower()
    
    # Count how many keywords are found
    found_keywords = [word for word in TRUCKING_KEYWORDS if word in email_lower]
    
    # Return True if at least one keyword is found
    if found_keywords:
        print(f"Found trucking-related keywords: {', '.join(found_keywords)}")
        return True
    else:
        print("No trucking-related keywords found in email")
        return False

def connect_to_email():
    """Connect to Gmail IMAP server using OAuth2 credentials."""
    print("Attempting to connect to email server...")
    credentials = get_credentials()
    if not credentials:
        raise Exception("No valid credentials found. Please log in again.")
        
    # Get the access token
    access_token = credentials.token
    
    # Connect to Gmail IMAP
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.authenticate('XOAUTH2', lambda x: f'user=me\x01auth=Bearer {access_token}\x01\x01')
    print("Successfully authenticated with Gmail")
    
    print("Selecting inbox...")
    mail.select("inbox")
    return mail

def fetch_unread_emails(mail):
    """Fetch IDs of unread emails from the last 24 hours in Primary category only."""
    print("Fetching unread emails from Primary category in the last 24 hours...")
    date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
    # First, search for unread emails in the date range
    search_criteria = f'(SINCE "{date}" UNSEEN)'
    _, search_data = mail.search(None, 'X-GM-RAW "in:inbox category:primary"', search_criteria)
    email_ids = search_data[0].split()
    print(f"Found {len(email_ids)} unread primary emails from the last 24 hours")
    return email_ids

def get_email_body(mail, email_id):
    """Extract the plain text body from an email."""
    print(f"Fetching body for email {email_id}...")
    _, data = mail.fetch(email_id, "(RFC822)")
    raw_email = data[0][1]
    msg = email.message_from_bytes(raw_email)
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
    return msg.get_payload(decode=True).decode(errors="ignore")

def process_emails():
    """Process unread emails and return their bodies, marking them as seen."""
    try:
        mail = connect_to_email()
        email_ids = fetch_unread_emails(mail)
        email_bodies = []
        
        for email_id in email_ids:
            body = get_email_body(mail, email_id)
            if body and is_trucking_related(body):
                print("Processing trucking-related email...")
                email_bodies.append(body)
                #mail.store(email_id, '+FLAGS', '\\Seen')  # Mark as seen
            else:
                print("Skipping non-trucking-related email")
                
        mail.logout()
        return email_bodies
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

if __name__ == "__main__":
    print("Starting email processing...")
    results = process_emails()
    print(f"Found {len(results)} trucking-related emails with content")
    for i, body in enumerate(results, 1):
        print(f"\nEmail {i}:")
        print("-" * 50)
        print(body[:200] + "..." if len(body) > 200 else body)
        print("-" * 50)