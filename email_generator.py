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

# --- MANDATORY CLOSING CONTENT ---
MANDATORY_CLOSING_LINE = "I am available to join immediately, as I have completed all my academic coursework."
CLOSING_BLOCK = (
    "\n\n"
    f"{MANDATORY_CLOSING_LINE}\n\n"
    "Best regards,\n"
    "Abhinav Prasad\n"
    # Placeholder contact information - replace with actual data in resume
    "Email: abhinavprasad2004ap@gmail.com\n"
    "Phone: 8989625663\n"
    "LinkedIn: https://www.linkedin.com/in/abhinav-prasad-0a894b251/\n"
    "GitHub: https://github.com/Abhii242004"
)
# ---------------------------------


def generate_application_email(job_description: str, resume_data: str) -> str:
    """
    Sends job and resume data to the LLM API to generate a personalized application email.
    
    Args:
        job_description: The text content of the job posting.
        resume_data: The text content of the applicant's resume.

    Returns:
        The generated email content (subject line + body) as a string, or None on failure.
    """
    
    # CRITICAL: We now require the LLM to end with a specific, unique phrase.
    system_prompt = (
        "You are a skilled applicant, Abhinav Prasad, applying for the target job. Your task is to write a highly tailored, "
        "professional application email to the hiring manager. The output must start with the Subject line, followed by the email body.\n\n"
        "Use the following rules:\n"
        "1. The email must be written **from the perspective of Abhinav Prasad**.\n"
        "2. The email must be concise (max 4-5 short paragraphs).\n"
        "3. **Critically analyze** the job requirements and **directly correlate** Abhinav's skills, projects, and work experience from the resume to the job requirements. Mention specific projects or achievements where possible.\n"
        "4. Include a compelling subject line at the very top, clearly separated (e.g., 'Subject: Inquiry about X Role').\n"
        "5. **CRITICAL STOP:** End the email body immediately after the final analytical paragraph with the unique phrase: `---END-OF-BODY---`.\n"
        "6. DO NOT include any closing line (like 'Sincerely', 'Best regards') or contact block, as these will be appended by the system.\n"
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

            # --- POST-PROCESSING: Append mandatory closing here ---
            
            # 1. Primary cleanup: Split content using the unique stop phrase (if the LLM obeyed the rule)
            stop_phrase = "---END-OF-BODY---"
            if stop_phrase in email_content:
                email_content = email_content.split(stop_phrase)[0].strip()
            
            # 2. Secondary cleanup (Aggressive): If the stop phrase was ignored, forcefully remove known closings and contact blocks
            
            # Known closing phrases the LLM often uses
            common_closings = ["Best regards,", "Sincerely,", "Thank you,", "I look forward to hearing from you."]
            
            # Aggressively try to remove the LLM's closing block
            for closing in common_closings:
                # Use rfind to find the last instance (usually the closing)
                idx = email_content.lower().rfind(closing.lower())
                if idx != -1 and len(email_content) - idx < 200: # Only cut if it's near the end
                    email_content = email_content[:idx].strip()
                    break # Stop after finding the first one

            # Further clean the end in case the LLM included the contact info
            # Check for email/phone pattern near the very end and strip it
            if "@" in email_content[-100:]:
                 # This is a heuristic: assume the last paragraph/block is the unwanted contact info
                 # Split by the last occurrence of two newlines (\n\n) to get the final block
                 parts = email_content.rsplit('\n\n', 1)
                 if len(parts) > 1 and ("@" in parts[1] or "+" in parts[1]):
                     email_content = parts[0].strip()
            
            # 3. Add a separation newline
            email_content += "\n\n"
            
            # 4. Append the guaranteed closing block
            return email_content + CLOSING_BLOCK
            # ----------------------------------------------------

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 and i < max_retries - 1:
                time.sleep(last_delay)
                last_delay *= 2
                continue
            else:
                return None
        except Exception as e:
            return None
            
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

