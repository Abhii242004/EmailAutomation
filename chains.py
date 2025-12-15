import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

load_dotenv()

class Chain:
    def __init__(self):
        # Using llama-3.3-70b-versatile for complex reasoning/writing tasks
        self.llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
        )
        
    def extract_jobs(self, cleaned_text):
        # This prompt extracts structured data (Title, Company, Skills) from the JD.
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT (JOB DESCRIPTION):
            {page_data}
            ### INSTRUCTION:
            The scraped text is a job description.
            Your job is to extract the job posting details and return them in JSON format containing the following keys: `title`, `company`, `role`, `experience`, `skills` and `description`.
            Ensure the JSON is valid and contains ALL provided keys. If a key is not explicitly mentioned, use "N/A".
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
        except OutputParserException:
            # Added more specific context to the error message
            raise OutputParserException("Could not parse the job description into structured JSON. Try shortening the input.")
        # Ensure the output is always iterable (a list), even if only one job is returned
        return res if isinstance(res, list) else [res]

    # CORRECTED: Function signature now accepts 'resume_data' instead of 'links'
    def write_mail(self, job, resume_data):
        # This prompt generates the final email using the extracted job details and the raw resume text.
        prompt_email = PromptTemplate.from_template(
            """
            ### CANDIDATE RESUME:
            {resume_data}

            ### TARGET JOB DETAILS (Extracted from JD):
            {job_description}

            ### INSTRUCTION:
            You are a skilled applicant, Abhinav Prasad, applying for the job detailed above. Your job is to write a highly tailored, professional application email to the hiring manager.
            
            Use the following rules:
            1. The email must be written **from the perspective of Abhinav Prasad**.
            2. The email must be concise (max 4-5 short paragraphs).
            3. **Critically analyze** the 'TARGET JOB DETAILS' and **directly correlate** Abhinav's skills, projects, and work experience from the 'CANDIDATE RESUME' to the job requirements. Mention specific projects or achievements where possible (e.g., mention the NAI tool project if the job requires Streamlit/AI skills).
            4. Include a compelling subject line at the very top, clearly separated.
            5. The email should end with a professional closing and Abhinav Prasad's full contact block (Email, Phone, LinkedIn/GitHub/Portfolio links if available in the resume).
            6. Do not provide a preamble or post-amble, only the email content.

            ### COLD EMAIL DRAFT:
            """
        )
        chain_email = prompt_email | self.llm
        # CORRECTED: Invoking the chain with the extracted job details and the raw resume text
        res = chain_email.invoke({"job_description": str(job), "resume_data": resume_data})
        return res.content
        

if __name__ == "__main__":

    # print(os.getenv("GROQ_API_KEY"))
