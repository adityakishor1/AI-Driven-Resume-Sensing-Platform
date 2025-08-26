import streamlit as st
import google.generativeai as genai
import os
import docx2txt
import PyPDF2 as pdf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("GOOGLE_API_KEY is not set. Check your environment variables.")
    st.stop()  # Stop execution if API key is missing

# Configure Google AI
genai.configure(api_key=API_KEY)

# Model configuration
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

# Safety settings
safety_settings = [
    {"category": f"HARM_CATEGORY_{category}", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    for category in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]
]

def generate_response_from_gemini(input_text):
    """Generates AI response from Gemini API"""
    try:
        llm = genai.GenerativeModel(
            model_name="gemini-1.5-pro",  # Use the latest model
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        output = llm.generate_content(input_text)
        return output.text if output.text else "No response generated."
    except Exception as e:
        return f"Error: {str(e)}"

def extract_text_from_pdf_file(uploaded_file):
    """Extracts text from PDF"""
    pdf_reader = pdf.PdfReader(uploaded_file)
    text_content = ""
    for page in pdf_reader.pages:
        text_content += str(page.extract_text())
    return text_content

def extract_text_from_docx_file(uploaded_file):
    """Extracts text from DOCX"""
    return docx2txt.process(uploaded_file)

# Prompt template
input_prompt_template = """
As an experienced Resume Screening AI Tool,  
with profound knowledge in technology, software engineering, data science,  
and big data engineering, your role involves evaluating resumes against job descriptions.  
Recognizing the competitive job market, provide top-notch assistance for resume improvement.  

Your goal is to analyze the resume against the given job description,  
assign a percentage match based on key criteria, and pinpoint missing keywords accurately.  

Resume: {text}  
Job Description: {job_description}  

I want the response in a single structured string with the following format:  
{{
  "Job Description Match": "%",  
  "Missing Keywords": "",  
  "Candidate Summary": "",  
  "Skills": "",  
  "Experience": ""  
}}
"""

# Streamlit UI
st.title("Resume Screening AI Tool")
st.markdown('<style>h1{color: orange; text-align: center;}</style>', unsafe_allow_html=True)

job_description = st.text_area("Paste the Job Description here!", height=300)
uploaded_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx"], help="Please upload a PDF or DOCX file")

submit_button = st.button("Submit")

if submit_button:
    if uploaded_file is not None:
        # Extract resume text
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf_file(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            resume_text = extract_text_from_docx_file(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a PDF or DOCX file.")
            st.stop()

        # Generate AI response
        response_text = generate_response_from_gemini(input_prompt_template.format(text=resume_text, job_description=job_description))

        st.subheader("Matching From Job Description")
        st.write(response_text)  # Display AI response

        # Extract Job Description Match percentage safely
        match_percentage = 0.0  # Default value
        if '"Job Description Match":"' in response_text:
            try:
                match_percentage_str = response_text.split('"Job Description Match":"')[1].split('"')[0]
                match_percentage = float(match_percentage_str.rstrip('%'))
            except (IndexError, ValueError):
                st.error("Error extracting match percentage from response.")

        # Display recommendation based on match percentage
        if match_percentage >= 80:
            st.success("✅ Move forward with hiring")
        else:
            st.warning("⚠️ Not a Match")
    else:
        st.error("Please upload a resume before submitting.")
