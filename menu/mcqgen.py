import os
import json
import PyPDF2
import pandas as pd
import traceback
from dotenv import load_dotenv
from src.mcqgenerator.utils import read_file, get_table_data
from src.mcqgenerator.logger import logging
import streamlit as st
from src.mcqgenerator.MCQGenerator import generate_evaluate_chain
with open(r"Response.json", 'r') as file:
    RESPONSE_JSON = json.load(file)
def main():
    

    st.title("QuizCraft: The MCQ Genie")

    # Initialize session state for quiz data and user answers
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = None
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'show_error' not in st.session_state:
        st.session_state.show_error = False

    def process_quiz_data(quiz_json):
        """Convert the nested JSON structure to a more manageable format"""
        processed_data = []
        quiz_dict = json.loads(quiz_json) if isinstance(quiz_json, str) else quiz_json
    
        for question_num, question_data in quiz_dict.items():
            processed_question = {
                'question_num': question_num,
                'mcq': question_data['mcq'],
                'options': question_data['options'],
                'correct': question_data['correct']
            }
            processed_data.append(processed_question)
    
        return processed_data

    def calculate_score():
        correct_answers = 0 
        total_questions = len(st.session_state.quiz_data)
        for i, question in enumerate(st.session_state.quiz_data):
            user_answer = st.session_state.user_answers.get(i)
            if user_answer and user_answer != 'Select an option':
                correct_answer = question['correct']
                if user_answer[0] == correct_answer:  # Compare just the letter
                    correct_answers += 1
        return correct_answers, total_questions

    def check_answers_complete():
        """Check if all questions have been answered"""
        total_questions = len(st.session_state.quiz_data)
        answered_questions = sum(1 for ans in st.session_state.user_answers.values() 
                               if ans != 'Select an option')
        return answered_questions == total_questions

    # Fi    le upload and quiz generation section
    if not st.session_state.quiz_data:
        with st.form("user_inputs"):
            uploaded_file = st.file_uploader("Upload a PDF or txt file")
            mcq_count = st.number_input("No. of MCQs", min_value=3, max_value=50)
            subject = st.text_input("Insert Subject", max_chars=20)
            tone = st.text_input("Complexity Level of Questions", max_chars=20, placeholder="Simple")
            button = st.form_submit_button("Create MCQs")

            if button and uploaded_file is not None and mcq_count and subject and tone:
                with st.spinner("loading..."):
                    try:
                        text = read_file(uploaded_file)
                        response = generate_evaluate_chain({
                            "text": text,
                            "number": mcq_count,
                            "subject": subject,
                            "tone": tone,
                            "response_json": json.dumps(RESPONSE_JSON)
                        })

                    except Exception as e:
                        traceback.print_exception(type(e), e, e.__traceback__)
                        st.error("Error")
                    else:
                        if isinstance(response, dict):
                            quiz_json_start = response['quiz'].find('{')
                            quiz_json_end = response['quiz'].rfind('}') + 1
                            quiz_json = response['quiz'][quiz_json_start:quiz_json_end]
                            if quiz_json:
                                try:
                                    processed_quiz_data = process_quiz_data(quiz_json)
                                    st.session_state.quiz_data = processed_quiz_data
                                    st.session_state.review = response.get("review", "")
                                except Exception as e:
                                    st.error(f"Error processing quiz data: {str(e)}")
                            else:
                                st.error("No valid quiz data found")

    # Quiz display and interaction section
    if st.session_state.quiz_data is not None and not st.session_state.quiz_submitted:
        st.subheader("Answer the following questions:")
        
        # Display error message if needed
        if st.session_state.show_error:
            st.error("Please answer all questions before submitting.")
            st.session_state.show_error = False
        
        with st.form("quiz_form"):
            for i, question in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{i+1}. {question['mcq']}**")
                
                # Create a list of options in the format "a) option_text"
                options = [f"{opt_key}) {opt_value}" 
                        for opt_key, opt_value in question['options'].items()]
                
                # Add an initial empty option to prevent default selection
                options = ['Select an option'] + options
                
                selected_option = st.radio(
                    f"Select your answer for question {i+1}:",
                    options,
                    key=f"q_{i}",
                    index=0  # Set default to first option (Select an option)
                )
                
                st.session_state.user_answers[i] = selected_option
            
            submit_quiz = st.form_submit_button("Submit Quiz")
            if submit_quiz:
                if check_answers_complete():
                    st.session_state.quiz_submitted = True
                else:
                    st.session_state.show_error = True
                    st.experimental_rerun()

    # Results display section
    if st.session_state.quiz_submitted:
        correct_answers, total_questions = calculate_score()
        st.session_state.score = (correct_answers / total_questions) * 100
        
        st.subheader("Quiz Results")
        st.write(f"Your Score: {st.session_state.score:.2f}%")
        st.write(f"Correct Answers: {correct_answers}/{total_questions}")
        
        st.subheader("Detailed Review")
        for i, question in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{i+1}. {question['mcq']}**")
            
            # Display all options
            for opt_key, opt_value in question['options'].items():
                if opt_key == question['correct']:
                    st.markdown(f"- {opt_key}) {opt_value} ✓ (Correct Answer)")
                elif opt_key == st.session_state.user_answers[i][0]:  # Compare with first character of answer
                    st.markdown(f"- {opt_key}) {opt_value} ❌ (Your Answer)")
                else:
                    st.markdown(f"- {opt_key}) {opt_value}")
            
            st.markdown("---")
        
        # if st.button("Start New Quiz"):
        #     st.session_state.quiz_data = None
        #     st.session_state.user_answers = {}
        #     st.session_state.quiz_submitted = False
        #     st.session_state.score = 0
        #     st.session_state.show_error = False
        #     st.experimental_rerun()
        def reset_quiz():
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.score = 0
            st.session_state.show_error = False
        if st.button("Start New Quiz"):
            reset_quiz()
