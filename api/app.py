import streamlit as st
import os
from utils import extract_paddle, save_files, justification, extract_format
import json
import pandas as pd
import shutil  # Import the shutil module for file/directory operations
import numpy as np  # Import numpy


st.set_page_config(
    page_title='HR ',
    layout="wide",
    
)
import time 

if "user_input_dict" not in st.session_state:
    st.session_state['user_input_dict'] = {'to': [], 'cc': [], 'bcc': []}

DEFAULT_DIR_PATH = "./"
files_path = os.path.join(DEFAULT_DIR_PATH, "files")

st.markdown("""
    <style>
        .top-bar {
            background-color: #C8AD7F;
            color: white;
            padding: 10px;
            font-size: 26px;
            text-align: left;
            border-radius: 5px 5px 0 0;
            position: relative;
            margin: -35px;
            font-weight: bold;
            margin-left: 26px;
            margin-right: 26px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }  
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-bar">
    <div>Resume Analysis Application</div>
</div>
""", unsafe_allow_html=True)

with open("css/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

c10,c7,c9,c8,c11 = st.columns((0.2,2,0.5,2,0.2))
with c7:
    st.write('Input')

    # Set the job description section style
    job_description_section_style = """
        <div style="font-size: 18px; color: #6c757d; display: flex; align-items: center;">
            <span style="font-weight: bold; margin-right: 10px;"><h2>Job Description</h2></span>
            <span style="font-weight: bold; margin-right: 700px; color: #6c757d; background-color: rgba(108, 117, 125, 0.2); padding: 2px 5px; border-radius: 3px; font-size: 14px;">Required</span>

        </div>
    """

    # # Render the job description section
    st.markdown(job_description_section_style, unsafe_allow_html=True)

    overall_query = st.text_area( ":information_source: Enter the job description you want to evaluate the candidate against.",height=150)

    # Set the resume description section style
    resume_section_style = """
        <div style="font-size: 18px; color: #6c757d; display: flex; align-items: center;">
            <span style="font-weight: bold; margin-right: 10px;"><h2> CV/Resume PDF File </h2></span>
            <span style="font-weight: bold; margin-right: 330px; color: #6c757d; background-color: rgba(108, 117, 125, 0.2); padding: 2px 5px; border-radius: 3px; font-size: 14px;">Required</span>

        </div>
    """
    # # Render the job description section
    st.markdown(resume_section_style, unsafe_allow_html=True)

    main_uploaded_files = st.file_uploader(":information_source:   Upload a PDF of the candidates resume/CV.", accept_multiple_files=True, type=["pdf"], )

    def delete_entity(index):
        st.session_state['text_boxes'] = [entity for i, entity in enumerate(st.session_state['text_boxes']) if i != index]
    
    # with open("style.css") as f:
    #     st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    if "text_boxes" not in st.session_state:
        st.session_state['text_boxes'] = []  

    if "is_submitting" not in st.session_state:
        st.session_state['is_submitting'] = False

    def submit():
        name = st.session_state.get('name_entity', "").strip()
        context = st.session_state.get('context_entity', "").strip()
        if name and context:
            # Check for duplicates before appending
            if (name, context) not in st.session_state['text_boxes']:
                st.session_state['text_boxes'].append((name, context))
            st.session_state['name_entity'] = ""
            st.session_state['context_entity'] = ""
            st.session_state['is_submitting'] = False

    def delete_entry(index):
        if index < len(st.session_state['text_boxes']):
            st.session_state['text_boxes'].pop(index)

    def update_entry(index, field):
        name = st.session_state.get(f'name_{index}', "")
        context = st.session_state.get(f'context_{index}', "")
        if name and context:
            st.session_state['text_boxes'][index] = (name, context)

    # Add a new empty row when "+ Add row" button is clicked
    if st.button("+ Add Extraction Entities"):
        st.session_state['text_boxes'].append(("", ""))
        st.session_state['is_submitting'] = False

    st.markdown("""
        <style>
            .stButton button {
                padding: 5px 10px;
                margin-top: 10px;
                margin-bottom: -50px;
            }
        </style>
    """, unsafe_allow_html=True)

    for i, (name, context) in enumerate(st.session_state['text_boxes']):
        # Initialize the session state for the name, type, and context input fields
        if f"name_{i}" not in st.session_state:
            st.session_state[f"name_{i}"] = name
        if f"context_{i}" not in st.session_state:
            st.session_state[f"context_{i}"] = context
        
        col1, col2, col3 = st.columns([7, 9, 3])
        with col1:
            Name = st.text_input(f"Entity{i+1}", st.session_state[f"name_{i}"], key=f"name_{i}", placeholder="Enter text...", on_change=update_entry, args=(i, 'name'))
        with col2:
            st.text_input(f"Description {i+1}*", st.session_state[f"context_{i}"], key=f"context_{i}", placeholder="Enter text...", on_change=update_entry, args=(i, 'context'))
        with col3:
            st.write(" ")

            if st.button("X", key=f"delete_{i}", on_click=delete_entry, args=(i,)):
                st.session_state['is_submitting'] = False

    st.write(
        """
        <style>
        button[kind="primary"] {
            background-color: #C8AD7F;
            color: white;
            border: none;
            border: 1px solid #000000;
            padding: 12px 24px;
            border-radius: 4px;
            font-size: 13px;
            font-family: 'Lato', sans-serif;
            cursor: pointer;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    score_buttom = st.button("Get Score",type="primary", use_container_width=True)

with c8:
    st.write("Output")
    if main_uploaded_files:
        main_saved_status = save_files(main_uploaded_files)

    def erro_submit():
        extract_values = st.session_state['text_boxes']
        
        if len(main_uploaded_files) > 0 and len(overall_query) > 0:
            with st.spinner("Extracting the text.. takes some time⏳"):
                start = time.time()
                result_df = {}
                times_df = {}
                document_names = []

                for main_uploaded_file in main_uploaded_files:
                    overall_start_time = time.time()
                    times_df[main_uploaded_file.name] = {}
                    main_file_path = f"{files_path}/{main_uploaded_file.name}"
                    document_names.extend([main_uploaded_file.name])

                    # Extract paddle
                    extract_paddle_start_time = time.time()
                    text = extract_paddle(main_file_path)
                    extract_paddle_end_time = time.time()
                    extract_paddle_time = extract_paddle_end_time - extract_paddle_start_time
                    times_df[main_uploaded_file.name]['extract_paddle'] = extract_paddle_time.tolist() if isinstance(extract_paddle_time, np.ndarray) else extract_paddle_time

                    # Justification
                    justification_start_time = time.time()
                    justification_text = justification(overall_query, text)
                    justification_end_time = time.time()
                    justification_time = justification_end_time - justification_start_time
                    times_df[main_uploaded_file.name]['justification'] = justification_time.tolist() if isinstance(justification_time, np.ndarray) else justification_time

                    # Extract format
                    extract_format_start_time = time.time()
                    final_result = extract_format(text, justification_text, extract_values)
                    final_result = final_result.lower()
                    extract_format_end_time = time.time()
                    extract_format_time = extract_format_end_time - extract_format_start_time
                    times_df[main_uploaded_file.name]['extract_format'] = extract_format_time.tolist() if isinstance(extract_format_time, np.ndarray) else extract_format_time
                    total_time = extract_paddle_time + justification_time + extract_format_time
                    times_df[main_uploaded_file.name]['total_time'] = total_time.tolist() if isinstance(total_time, np.ndarray) else total_time
                    dict_result = json.loads(final_result)

                    for key in dict_result.keys():
                        if key not in result_df:
                            result_df[key] = []
                        result_df[key].append(dict_result[key])

                res_df = pd.DataFrame(result_df)
                times_df = pd.DataFrame.from_dict(times_df)
                res_df["Document Name"] = document_names
                res_df.columns = [col.upper() for col in res_df.columns]
                csv = res_df.to_csv(index=False)
                res_df["LINKEDIN"] = res_df["LINKEDIN"].apply(lambda x: f'<a href="{x}">{x}</a>')
                res_df = res_df.style.set_properties(**{f'td[{i}]': {'title': res_df[col]} for i, col in enumerate(res_df.columns)})

                styled_df = res_df.to_html(escape=False, index=False)

                html_table = f"""
                    <div style="overflow-x: auto; margin-bottom: 20px;">
                    <style>
                    table {{
                        margin-left: auto;
                        margin-right: auto;
                        font-family: Arial, sans-serif;
                        font-size: 14px;
                        color: #333333;
                        border-collapse: collapse;
                        width: 80%;
                        table-layout: auto;
                    }}
                    th, td {{
                        padding: 4px 8px;
                        text-align: left;
                        vertical-align: middle;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        position: relative;
                    }}
                    th {{
                        font-weight: bold;
                        background-color: #f2f2f2;
                        color: #333333;
                        text-align: center;
                    }}
                    td:hover::before {{
                        content: attr(title);
                        position: absolute;
                        z-index: 1;
                        background-color: rgba(0, 0, 0, 0.8);
                        color: white;
                        padding: 5px;
                        border-radius: 4px;
                        white-space: pre-wrap;
                        max-width: 300px;
                        overflow-wrap: break-word;
                        left: 50%;
                        transform: translateX(-50%);
                        top: -5px;
                        transform: translateY(-100%);
                    }}
                    </style>
                    {styled_df}
                    </div>
                    """

                st.markdown(html_table, unsafe_allow_html=True)

                end = time.time()
                time_taken = end - start
                times_df = pd.DataFrame.from_dict(times_df)

                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name='resume_scores.csv',
                    mime='text/csv',
                )
                st.session_state['text_boxes'] = []

                for filename in os.listdir(files_path):
                    file_path = os.path.join(files_path, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        st.write(f"Failed to delete {file_path}. Reason: {e}")
        else:
            st.warning("Please upload the Job Description and Resume", icon="⚠️")

    if score_buttom:
        if len(main_uploaded_files) >0 and   len(overall_query) >0:
            try:
                erro_submit()
            except Exception as e:
                st.error(f"An error occurred: {e}")
                erro_submit()

        else:
            st.warning("Please upload the Job Description and Resume", icon="⚠️")
