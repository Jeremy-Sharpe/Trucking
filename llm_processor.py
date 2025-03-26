import requests
import json
from config import LLM_API_KEY
import google.generativeai as genai




def extract_data_with_llm(email_body, fields_to_extract):
    """Use Google's Generative AI to extract logistics data with context."""
    # Configure the generative AI
    genai.configure(api_key=LLM_API_KEY)
    
    # Create the prompt with dynamic fields
    fields_str = ", ".join(fields_to_extract)
    prompt = (
        "From the following email, extract the following fields: " + fields_str + ". "
        "For each piece of information, also provide the exact phrase or sentence from the email that contains this information. "
        "Format the output as a JSON object where each key (e.g., 'shipment_id', 'origin') has a sub-object with 'value' (the extracted information) "
        "and 'context' (the relevant phrase or sentence from the email).\n\n"
        "If you cannot find the information, respond with 'N/A' for the value and the context should be empty. "
        "You must respond with ONLY valid JSON, no other text. Do not include any other text or comments in your response. ONLY respond with valid JSON. Do not add any thing like json before the actual json response. "
        f"Email:\n{email_body}"
    )

    try:
        # Generate content using Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Parse the response
        if response.text:
            try:
                textResponse = response.text.replace("```json", "").replace("```", "").strip()
                json_data = json.loads(textResponse)
                
                # Check if all fields are N/A
                all_na = True
                for field_data in json_data.values():
                    if isinstance(field_data, dict) and field_data.get('value') != 'N/A':
                        all_na = False
                        break
                
                # Skip this entry entirely if all fields are N/A
                if all_na:
                    print("Skipping email - no valid data found")
                    return None
                
                return json_data
                
            except json.JSONDecodeError:
                print("LLM response is not valid JSON:", response.text)
                return None
        else:
            print("No response from LLM")
            return None
            
    except Exception as e:
        print(f"Error calling LLM API: {str(e)}")
        return None

if __name__ == "__main__":
    email_body = "test"
    test_fields = ['shipment_id', 'origin', 'destination']
    result = extract_data_with_llm(email_body, test_fields)
    if result:  # Only print if we have valid data
        print(result)