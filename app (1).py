import os
import time
import langchain
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import pytesseract as pyt
from tavily import TavilyClient
from langchain.messages import SystemMessage , HumanMessage
import numpy as np
import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
from PIL import Image
import base64

# steream lit is web based pyhton frame work 
st.title ("AI RESUME MAKER & JOB APPLY AGENT")
st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrGg1PzVvppycJgP2W8V_0eYflg5xcVNxXXYn3OlOGUP6JDnu9O_SZnks&s=10",
        width=300)
# api keys
GOOGLE= st.sidebar.text_input("GEMINI",type="password")
GROQ= st.sidebar.text_input("GROQ",type="password")
TAVILY =st.sidebar.text_input("TAVILY",type="password")

if not (GOOGLE) and not (GROQ) and not (TAVILY):
    st.sidebar.warning("pass api keys")
    st.stop()
else:
    st.success("API KEYS LOADED")
    
#====================================================
model=ChatGoogleGenerativeAI(
    google_api_key=GOOGLE,
    model='gemini-3.5-flash-lite',
    temperature=1
)
def search_jobs(query):
  """this function helps to find recent news or recent jobs related to given search query suppose user to write a python develpoer or should return trending news and job links """
  tavily_client = TavilyClient(api_key=TAVILY)
  return tavily_client.search(query)
agent = create_agent(
        model = model,
  tools = [search_jobs]
)

#================PROMPT GEN=================
def prompt_generator(agent):
  """This function help yo give detailed prompt
  followed by chain thoughts and
  persona based prompting, main task is to give
  detailed prompt to uild resume for
  students or experienced person
  Based on their given personal information."""

  prompt = """ You are a senior HR resume analyzer,
 main task is to give
  detailed prompt to uild resume for
  students or experienced person
  Based on their given personal information.
  System Instructions I want model to genrate resume
  in HTML format, include that in prompt"""

  response = agent.invoke(prompt)
  file_name = 'prompt.py'
  with open(file_name,'w') as f:
    f.write(response.content [-1] ['text'])
  return "Prompt file generated Successfult, agent can read it"
#resume maker prompt
prompt_generator(model)
def resume():
  """this function gives updated prompt for model """
  with open('prompt.py','r') as f:
    prompt=f.read()
  return prompt
resume()

#=======================IMAGE UPLOADER==============================
# ==================== UPLOAD IMAGE ====================

FILE = st.sidebar.file_uploader(
    "Choose an image file",
    type=["jpg", "jpeg", "png", "webp"]
)

if FILE is not None:
    try:
        image = Image.open(FILE)

        st.sidebar.image(image, 
                         caption="Uploaded Image", 
                         use_container_width=True)

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        base_name = os.path.splitext(FILE.name)[0]
        save_path = f"{base_name}.jpg"

        image.save(save_path, "JPEG")
        st.sidebar.success(f"🎉 Image successfully saved as `{save_path}`!")

    except Exception as e:
        st.error(f"Error processing image: {e}")

#===============RESUME GENERATOR =============
#===============RESUME GENERATOR =============
prompt="""you are a helpful ai assistant  with a job resume maker , your task is to give html gormat resume ,with a proper designing using recent html js css code , with professional degsine format , user will upload data and return html format resume make it diffrent colour scheme andthe resume should project m skill set  also make it look like professional , create side margins table also make the text gradient for heddings like professional summary
IMPORTANT: wherever the profile photo goes in the resume, output exactly this tag and nothing else:
<img src="PROFILE_IMAGE_PLACEHOLDER" style="width:100px;height:100px;border-radius:50%;">
do not draw or generate any other image tag or placeholder circle yourself """
final_prompt=prompt+resume()

USER_INFO=st.text_area("ENTER YOUR INFORMATION")

user_details=f"""user details:given below :
resume info {USER_INFO} 
DEFAULT IF NOT GIVEN : PYTHON DEVELOPER RESUME"""

query = final_prompt+user_details

OPTIONS = ["DELHI","NOIDA","GURGAON/GURUGRAM",
          'KANPUR','LUCKNOW','BANGLORE','PUNE']
           
LOCATION = st.sidebar.multiselect('SELECT LOCATION: ',
                                    options = OPTIONS )

JOB_PROFILE = ["PYTHON DEVELOPER",'GEN AI',
                'FULL-STACK DEVELOPER','DATA ANALYST']

PROFILE = st.sidebar.multiselect("SELECT JOB ROLE",
                options = JOB_PROFILE)

job_prompt = f"""Based on {PROFILE} jobs in {LOCATION}, I 
want latest job news in using tavily, 
try top 10 search or whatever available
and give result like naukri theme design with
job name, job desc, salary,
apply link and OUTPUT must be In HTML no markdowns"""

if st.button('generate resume'):
  with st.spinner("Running Agent"):

    response = agent.invoke({'messages': [{'role':'user','content':query}]})
    code=response['messages'][-1].content[-1]['text']
          
    if FILE is not None:
        with open(save_path, "rb") as img_file:
            b64_image = base64.b64encode(img_file.read()).decode()
        data_uri = f"data:image/jpeg;base64,{b64_image}"
        code = code.replace("PROFILE_IMAGE_PLACEHOLDER", data_uri)

    st.html(code , width="stretch" , unsafe_allow_javascript=True)
          
# ================ APPLY LIVE JOBS======================
    st.divider()
    response = agent.invoke({'messages':[{'role':'user','content':job_prompt}]})
    job_code = response['messages'][-1].content[-1]['text']
    st.html(job_code , width="stretch" , unsafe_allow_javascript=True)
