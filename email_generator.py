import requests
import json
import time
import sys

# --- Configuration ---
# NOTE: Replace with your actual Gemini/Groq API Key if you are running this locally.
# Assuming the Chain class uses the same configuration found in chains.py
GEMINI_API_KEY = ""
MODEL_NAME = "llama-3.3-70b-versatile" # Aligning model name with chains.py
API_URL = f"https://api.groq.com/openai/v1/chat/completions" # Using Groq API endpoint


def generate_application_email(job_description: str, resume_data: str) -> str:
    """
    Sends job and resume data to the LLM API to generate a personalized application email.
    
    Args:
        job_description: The text content of the job posting.
        resume_data: The text content of the applicant's resume.

    Returns:
        The generated email content (subject line + body) as a string, or None on failure.
    """
    
    system_prompt = (
        "You are a skilled applicant, Abhinav Prasad, applying for the target job. Your task is to write a highly tailored, "
        "professional application email to the hiring manager. The output must start with the Subject line, followed by the email body.\n\n"
        "Use the following rules:\n"
        "1. The email must be written **from the perspective of Abhinav Prasad**.\n"
        "2. The email must be concise (max 4-5 short paragraphs).\n"
        "3. **Critically analyze** the job requirements and **directly correlate** Abhinav's skills, projects, and work experience from the resume to the job requirements. Mention specific projects or achievements where possible.\n"
        "4. Include a compelling subject line at the very top, clearly separated (e.g., 'Subject: Inquiry about X Role').\n"
        "5. The email should end with a professional closing and Abhinav Prasad's full contact block (Email, Phone, LinkedIn/GitHub/Portfolio links).\n"
        "6. **MANDATORY CLOSING LINE:** You must include the following line immediately before the professional closing (e.g., 'Sincerely', 'Best regards'): 'I am available to join immediately, as I have completed all my academic coursework.'\n"
        "7. Do not provide a preamble or post-amble, only the email content."
    )

    user_query = (
        f"Generate the application email. Target Job Description:\n\n---\n{job_description}\n---\n\n"
        f"Candidate Resume:\n\n---\n{resume_data}\n---"
    )

    # Groq API payload (using Chat Completions format)
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0
    }

    # API Call with Exponential Backoff
    last_delay = 1
    max_retries = 4
    
    print(f"Connecting to {MODEL_NAME} API and drafting email...")

    for i in range(max_retries):
        try:
            response = requests.post(
                API_URL, 
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {GEMINI_API_KEY}' # Using environment variable if set
                }, 
                data=json.dumps(payload)
            )
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            result = response.json()
            
            # Extract the raw text from the response
            email_content = result.get('choices', [{}])[0].get('message', {}).get('content')
            
            if not email_content:
                raise ValueError("Received empty content from the model.")

            return email_content

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 and i < max_retries - 1:
                print(f"Rate limit hit. Retrying in {last_delay} seconds...")
                time.sleep(last_delay)
                last_delay *= 2
                continue
            else:
                print(f"HTTP Error: {e}")
                print(f"Response body: {response.text}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
            
    print("Failed to call LLM API after multiple retries.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python email_generator.py <JOB_DESCRIPTION_FILE> <RESUME_FILE>")
        print("Example: python email_generator.py jd.txt resume.txt")
        sys.exit(1)

    jd_file_path = sys.argv[1]
    resume_file_path = sys.argv[2]
    
    try:
        with open(jd_file_path, 'r') as f:
            job_description = f.read().strip()
    except FileNotFoundError:
        print(f"Error: Job description file not found at {jd_file_path}")
        sys.exit(1)

    try:
        with open(resume_file_path, 'r') as f:
            resume_data = f.read().strip()
    except FileNotFoundError:
        print(f"Error: Resume file not found at {resume_file_path}")
        sys.exit(1)

    if not job_description or not resume_data:
        print("\nBoth job description and resume content must be provided. Exiting.")
        sys.exit(1)

    print("\n--- Starting Personalized Email Generation ---")
    
    email_draft = generate_application_email(job_description, resume_data)

    if email_draft:
        print("\n" + "="*50)
        print("PERSONALIZED APPLICATION EMAIL DRAFT")
        print("="*50)
        print(email_draft)
        print("\n" + "="*50)
    else:

        print("\nCould not generate the email draft. Check the console for error details.")
