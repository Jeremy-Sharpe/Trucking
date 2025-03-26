def test_email_import():
    """Test function to verify email module import is working correctly."""
    print("Testing email module import...")
    try:
        import email
        print("Email module imported successfully.")
        print("Testing message_from_bytes function...")
        test_bytes = b'Subject: Test\n\nTest Body'
        msg = email.message_from_bytes(test_bytes)
        print(f"Created message: {msg}")
        print("Test successful!")
    except Exception as e:
        print(f"Error importing email module: {e}")

if __name__ == "__main__":
    test_email_import() 