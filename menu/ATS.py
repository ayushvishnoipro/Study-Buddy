import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from dotenv import load_dotenv
from streamlit_lottie import st_lottie
import json
import os

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

def main():
    st.write("<h1><center>Applicant tracking systems</center></h1>", unsafe_allow_html=True)
    st.text("👉🏻                  Personal ATS for Job-Seekers & Recruiters                   👈")
    
    # Load the animation
    with open('src/ATS.json') as anim_source:
        animation = json.load(anim_source)
    st_lottie(animation, 1, True, True, "high", 200, -200)

    # Job role input
    st.text_input("Job Role")

    # Job description input
    desc = st.text_area("Paste the Job Description")

    # File upload for resume
    uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Pls Upload PDF file Only")

    # Submit button
    submit = st.button("Submit")

    if submit:
        if uploaded_file is not None:
            # Reading the uploaded PDF file
            reader = pdf.PdfReader(uploaded_file)
            text = ""
            for page_number in range(len(reader.pages)):
                page = reader.pages[page_number]
                text += str(page.extract_text())

            # Creating the input prompt for the generative AI
            input_prompt = f'''
            You're a skilled ATS (Applicant Tracking System) Scanner with a deep understanding of tech roles, software development, 
            tech consulting, and understand the ATS role in-depth. Your task is to evaluate the resume against the given description. 
            You must consider that the job market is crowded with applications and you should only pick the best talent. 
            Thus, assign the percentage & MissingKeywords with honesty & accuracy.
            resume: {text}
            description: {desc}
            I want an output in one single string having the structure: {{"PercentageMatch": "%", "MissingKeywordsintheResume": [], "ProfileSummary": ""}}.
            '''

            # Spinner while evaluating
            with st.spinner("Evaluating Profile..."):
                response = model.generate_content(input_prompt)

            # Parse the response data
            response_data = json.loads(response.text)

            # Display the ATS scanner results
            st.subheader("ATS Scanner Dashboard")
            st.subheader("Candidate Evaluation Results")
            st.text(f"Percentage Match: {response_data['PercentageMatch']}")
            st.subheader("Missing Keywords in the Resume")
            for keyword in response_data['MissingKeywordsintheResume']:
                st.text(keyword)
            st.subheader("Profile Summary")
            st.markdown(response_data['ProfileSummary'])

if __name__ == "__main__":
    main()
