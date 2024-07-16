
# from paddleocr import PaddleOCR
# import cv2
import os, shutil
import re
import numpy as np
import pypdfium2 as pdfium
from langchain.chat_models import ChatOpenAI
import streamlit as st
import concurrent.futures
import pdfplumber
from PIL import Image
from typing import Optional, List

os.environ['OPENAI_API_KEY'] = ""

# class CustomOpenAI(ChatOpenAI):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)

#     def completion_with_retry(
#         self, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any
#     ) -> Any:
#         """Use tenacity to retry the completion call."""
#         if is_openai_v1():
#             return self.client.create(**kwargs)

#         retry_decorator = _create_retry_decorator(self, run_manager=run_manager)

#         @retry_decorator
#         def _completion_with_retry(**kwargs: Any) -> Any:
#             return self.client.create(**kwargs)

#         return _completion_with_retry(**kwargs)

# def client():
#     from typing import List
#     from openai import OpenAI
#     openai_api_base = "https://api.aimlapi.com/v1"

#     aiml_client = OpenAI(
#         api_key="EMPTY",
#         base_url=openai_api_base,
#     )
#     return aiml_client

# aiml_client = client()

llm_model = ChatOpenAI(model="gpt-4o",openai_api_key=os.getenv("OPENAI_API_KEY"),temperature=0.0, openai_api_base="https://api.aimlapi.com/v1")

# For OCR Resumes
# ocr = PaddleOCR(use_angle_cls=True, lang='en',
#                 show_log=False, det_model_dir="en_PP-OCRv3_det_infer/",
#                 rec_model_dir="en_PP-OCRv4_rec_infer/")

# def extract_paddle(doc_path):
#     if doc_path.endswith(".pdf"):
#         pdf = pdfium.PdfDocument(doc_path)
#         all_text = ""

#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             futures = [] 
#             for i in range(len(pdf)):
#                 page = pdf.get_page(i)
#                 pil_image = page.render(scale=300/72).to_pil()
#                 cv_image = np.array(pil_image)
#                 futures.append(executor.submit(ocr.ocr, cv_image, cls=True))
#                 for future in concurrent.futures.as_completed(futures):
#                     result = future.result()
#                     text = ""
#                     for res in result:
#                         for line in res:
#                             text += (str(line[-1][0])) + "\n"
#                     all_text += text

#             result = ocr.ocr(cv_image, cls=True)
#             text = ""
#             for res in result:
#                 for line in res:
#                     text += (str(line[-1][0])) + "\n"
#             all_text += text
#         return all_text
DEFAULT_DIR_PATH = "./"
files_path = os.path.join(DEFAULT_DIR_PATH, "files")

def extract_paddle(pdf_file):
    # Open the PDF file
    with pdfplumber.open(pdf_file) as pdf:
        # Initialize an empty string to store the extracted text
        text = ""

        # Loop through each page in the PDF
        for page in pdf.pages:
            # Extract the text from the current page
            page_text = page.extract_text()

            # Append the page text to the overall text
            text += page_text
    # print(f"extacted content is :-   {text}")
    return text

def save_files(files_list):
    if not os.path.exists(files_path):
        # os.system(f"mkdir {files_path}")
        os.mkdir(files_path)
    if os.path.exists(files_path):
        # Iterate over all files and directories in the folder
        for filename in os.listdir(files_path):
            file_path = os.path.join(files_path, filename)
            try:
                # Check if it's a file or directory and remove accordingly
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Remove the file or link
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove the directory and its contents
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        print(f'The folder {files_path} does not exist.')
    for file in files_list:
        file.name = file.name.replace(" ","_")
        save_path = f"{files_path}/{file.name}"
        pattern = re.compile(".pdf")
        match = re.search(pattern, save_path)
        if match:
            with open(save_path, mode='wb') as w:
                w.write(file.getvalue())
        else:
            im = Image.open(file)
            im.save(save_path)
    return True


# def calculate_responsibility_score(responsibility_query, text):
#     prompt = f"Given the following job description and resume text, rate how well the responsibilities/experience in the resume match the responsibilities outlined in the job description. Provide a score between 0 and 10, where 0 means no match and 10 means a perfect match.\n\nJob Description Responsibilities:\n{responsibility_query}\n\nResume Text:\n{text}. Please note only to give the score and nothing else"
#     support_template = """{question}"""
#     response = llm_model.predict(support_template.format(question=prompt))
#     responsibility = response
#     return responsibility

# def calculate_requirement_score(requirements_query, text):
#     prompt = f"Given the following job description requirements and resume text, rate how well the qualifications and skills in the resume match the requirements outlined in the job description. Provide a score between 0 and 10, where 0 means no match and 10 means a perfect match.\n\nJob Description Requirements:\n{requirements_query}\n\nResume Text:\n{text}.Please note only to give the score and nothing else"
#     support_template = """{question}"""
#     response = llm_model.predict(support_template.format(question=prompt))
#     requirement = response
#     return requirement

def justification(overall_query, text):
    prompt = f"Given the following job description requirements and resume text, rate how well the qualifications and skills in the resume match the requirements outlined in the job description. Suggest a score between 0 and 10, where 0 means no match and 10 means a perfect match. Please understand the resume ie the person and see if he is suitable for the job. Dont just do keyword search please. \n\nJob Description Requirements:\n{overall_query}\n\nResume Text:\n{text}.Please note only to give the justification for the score in 20 words and nothing else. And score as single digit ie no fraction way. "
    support_template = """{question}"""
    response = llm_model.invoke(support_template.format(question=prompt))
    justification = response
    # st.text(justification)
    return justification

# def calculate_overall_score(overall_query, text):
#     prompt = f"Given the following job description and resume text, rate the overall match between the responsibilities, requirements, and qualifications outlined in the job description and the experience, skills, and qualifications present in the resume. Provide an overall score between 0 and 10, where 0 means no match and 10 means a perfect match.\n\nJob Description:\n{overall_query}\n\nResume Text:\n{text}Please note only to give the score and nothing else"
#     support_template = """{question}"""
#     response = llm_model.predict(support_template.format(question=prompt))
#     overall = response
#     return overall
# removed ",res_score,req_score," from the line 73
# removed "Responsibility_Score is {res_score}. Requirement_Score is {req_score}." from line 77
# removed "5. Responsibility_Score 6. Requirement_Score" FROM 84 AND 85
def extract_format(text,justification_text,extract_values):
    prompt =f"""
    You are an Extraction Specialist of Resume. Extract the Name, Mobile No.,Email, LinkedIn, Overall Score, Justifcation, {f"entity: {vals[0]} entity_description: {vals[1]}" for vals in extract_values} from the resume.
    Resume is {text}. 
    
    Overall Score and Justication Text {justification_text} .

    Exected Output format:-
    Name: 
    Mobile No : 
    Email: 
    LinkedIn: 
    Overall Score: 
    Justification: 
    
    If any of the extraction content doesnt have value give it as NA.
    Also make sure the result doesnt have any array or dictionary or list etc tupe of format 
    Please note the output should be in json format and nothing else. no symbols or anything.
    """
    support_template = """{question}"""
    # st.text(prompt)
    response = llm_model.predict(support_template.format(question=prompt))

    if '```' in response:
        response = response.split('```')[1].replace('json', "").replace('JSON',"")
    # print(final)
    # st.text(final)
    return response
