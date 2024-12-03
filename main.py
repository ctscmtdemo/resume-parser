import os
import json
import PyPDF2 as pdf
import streamlit as st
import google.generativeai as genai

# Configure the Generative AI model
my_secret = os.environ['GOOGLE_API_KEY']
genai.configure(api_key=my_secret)
model = genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="Smart Application Tracking System",
                   page_icon=":robot:")


# Prompt Template
def create_prompt(resume_text, job_description):
    return f"""
    You are a skilled ATS (Application Tracking System) expert with deep knowledge of tech fields, software engineering, data science,
    data analysis, and big data engineering. Your task is to evaluate the resume based on the given job description. 
    Provide the matching percentage, identify missing keywords, and suggest improvements.

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    I want the response in the following sections:
    • Job Description Match: 
    • Missing Keywords: 
    • Profile Summary: 
    • Category Breakdown:
    • Matching breakdown:
    """


def extract_scores(resume_text, job_description):
    return f"""
    You are a skilled ATS (Application Tracking System) expert with deep knowledge of tech fields, software engineering, data science,
    data analysis, and big data engineering. Your task is to evaluate the resume based on the given job description. 
    Please provide the following scores in JSON format for the categories below, including an average score.

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Expected response format:
    {{
        "scores": {{
            "Technical Skills": <score>,
            "Research Experience": <score>,
            "Education Qualification": <score>,
            "Communication and Leadership": <score>,
            "Industry Knowledge": <score>,
            "Average Score": <average_score>
        }}
    }}
    """


# Function to analyze soft skills and cultural fit
def analyze_soft_skills_and_fit(resume_text, jd_text):
    prompt = f"""
    Based on the following resume and job description, analyze the candidate's soft skills and cultural fit. 

    Resume:
    {resume_text}

    Job Description:
    {jd_text}

    Please list the soft skills relevant to the job and provide a brief analysis of the candidate's cultural fit.
    """
    response = model.generate_content(prompt)
    return response.text


# Function to extract missing keywords
def extract_missing_keywords(resume_text, jd_text):
    jd_keywords = set(jd_text.lower().split())
    resume_keywords = set(resume_text.lower().split())
    missing_keywords = jd_keywords - resume_keywords
    return list(missing_keywords)


# Function to generate mock interview questions
def generate_mock_questions(resume_text, jd_text):
    prompt = f"""
    Based on the following resume and job description, generate relevant mock interview questions for the candidate.

    Resume:
    {resume_text}

    Job Description:
    {jd_text}

    Please provide a list of interview questions tailored to the role.
    """
    response = model.generate_content(prompt)
    return response.text


# Streamlit app
st.title("Smart Application Tracking System for Interviews")
st.text("Improve Your Resume ATS Score")

jd = st.text_area("Paste the Job Description", height=100)
uploaded_file = st.file_uploader("Upload Your Resume",
                                 type="pdf",
                                 help="Please upload the PDF")

# Create a two-column layout for user input
col1, col2 = st.columns(2)

with col1:
    min_years_experience = st.slider("Minimum Years of Experience", 0, 20, 7)

with col2:
    min_match_threshold = st.slider("Overall Matching Threshold Percentage", 0,
                                    100, 60)

submit = st.button("Submit")

if submit:
    with st.spinner("Analyzing your resume..."):
        if uploaded_file is not None:
            try:
                reader = pdf.PdfReader(uploaded_file)
                extracted_text = ""
                for page in reader.pages:
                    extracted_text += page.extract_text() or ""

                if not extracted_text.strip():
                    st.error(
                        "The uploaded PDF is empty. Please check your file.")
                else:
                    # Extract missing keywords
                    missing_keywords = extract_missing_keywords(
                        extracted_text, jd)

                    # Create the prompt for analysis
                    prompt = create_prompt(extracted_text, jd)

                    # Call the model to generate the response
                    response = model.generate_content(prompt)

                    # Process scores using the extract_scores function
                    scores_prompt = extract_scores(extracted_text, jd)
                    scores_response = model.generate_content(scores_prompt)

                    # Safely parse the scores response
                    try:
                        cleaned_response = scores_response.text.replace(
                            '```json', '').replace('```', '').strip()
                        scores_data = json.loads(cleaned_response)
                        scores = scores_data.get("scores", {})

                        # Calculate overall matching percentage
                        overall_match = scores.get(
                            "Average Score",
                            sum(scores.values()) / len(scores))

                        # create column
                        col3, col4 = st.columns(2)

                        # # Display results
                        # with col3:

                        with col4:
                            # Display decision based on overall match
                            st.markdown("### Decision:")
                            if overall_match >= min_match_threshold:
                                st.markdown(
                                    '<p style="color:green;">### Accepted</p>',
                                    unsafe_allow_html=True)
                            else:
                                st.markdown(
                                    '<p style="color:red;">### Rejected</p>',
                                    unsafe_allow_html=True)
                        st.write(response.text)
                        # Display category breakdown
                        st.markdown("### Category Breakdown:")
                        for category, score in scores.items():
                            st.write(f"- **{category}:** {score:.2f}")

                        # Display soft skills and cultural fit analysis
                        fit_analysis = analyze_soft_skills_and_fit(
                            extracted_text, jd)
                        st.markdown("### Soft Skills & Cultural Fit:")
                        st.write(fit_analysis)

                        # Generate resume improvement suggestions
                        improvement_suggestions_prompt = f"""
                        Based on the following resume and job description, suggest improvements to the resume.

                        Resume:
                        {extracted_text}

                        Job Description:
                        {jd}

                        Provide specific suggestions to enhance the resume's alignment with the job description.
                        """
                        improvement_suggestions = model.generate_content(
                            improvement_suggestions_prompt)
                        st.markdown("### Resume Improvement Suggestions:")
                        st.write(improvement_suggestions.text)

                        # Display mock interview questions
                        mock_questions = generate_mock_questions(
                            extracted_text, jd)
                        st.markdown("### Mock Interview Questions:")
                        st.write(mock_questions)

                    except json.JSONDecodeError:
                        st.error(
                            "Error parsing scores from the model's response.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.error("Please upload a resume and provide a job description.")
