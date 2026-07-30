import streamlit as st
import os
import time
import langchain
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from tavily import TavilyClient
import pytesseract as pyt
import numpy as np
from langchain.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent
from PIL import Image
import base64
import tempfile
st.set_page_config(layout="wide")

# =========================FRONTEND==================
st.title("AI RESUME MAKER & JOB APPLY AGENT")
st.image("https://www.madrona.com/wp-content/uploads/2024/05/AI-Agent-infrastructure-blog-post-ChatGPT.webp",
         width=400)
# api keys
GOOGLE= st.sidebar.text_input("Google", type = 'password')
GROQ= st.sidebar.text_input("GROQ ", type = 'password')
TAVILY= st.sidebar.text_input("TAVILY ", type = 'password')

if not (GOOGLE) and not(GROQ) and not (TAVILY):
  st.sidebar.warning("pass api keys")
  st.stop()
else:
  st.success("API KEYS LOADED")

# ============= MODEL and AGENT CODE====================
# tool 1
def search_latest_news_jobs(query):
  """This function helps to get
  latest news or latest jobs
  related to user given query
  using tavily"""

  from tavily import TavilyClient
  client = TavilyClient(api_key = TAVILY_API_KEY)
  return client.search(query)


# Step 4: Model and Agent creation
model1 = ChatGoogleGenerativeAI(
    model = "gemini-3.5-flash-lite",
    google_api_key = GOOGLE_API_KEY
)

model2 = ChatGroq(
    model = "qwen/qwen3.6-27b",
    groq_api_key = GROQ_API_KEY
)


#============Agent with tool==============
agent = create_agent(
    model = model1,   # can be model2 also,
    tools = [search_latest_news_jobs]
)


# Let's Generate Prompt for Resume using model

def prompt_generator():
  prompt = """You are a helpful AI Resume
  maker, I want you to use chain-of-thoughts
  and give detailed prompt for model
  where user want to generate resume
  for fresher or experienced one
  in HTML format, you have to give proper
  set of instructions, and make sure to keep
  design professional"""

  response = model1.invoke(prompt)
  prompt_ans = response.content[-1]['text']
  # print(prompt_ans)

  file_name = 'prompt.txt'
  with open(file_name, 'w') as f:
    f.write(prompt_ans)

prompt_generator()

# Final_Agent
#Tool 2
def prompt_reader():
  with open('prompt.txt','r') as f:
    prompt = f.read()
  return prompt

prompt = """you are a helpful ai assistant  with a job resume maker , your task is to give html format resume,
with a proper designing using recent html js css code , with professional degsine format , user will upload data and
return html format resume make it diffrent colour scheme andthe resume should project m skill set  also make it look
like professional , create side margins table also make the text gradient for heddings like professional summary
IMPORTANT: wherever the profile photo goes in the resume, output exactly this tag and nothing else:
<img src="PROFILE_IMAGE_PLACEHOLDER" style="width:100px;height:100px;border-radius:50%;">
do not draw or generate any other image tag or placeholder circle yourself"""
final_prompt = prompt + prompt_reader()

#============IMAGE UPLOAD===========
#===================UPLOAD IMAGE==============
FILE= st.sidebar.file_uploader(
   "Choose an image file",
   type=["jpg","jpeg","png","webp"]
)
if FILE is not None:
   try:
      image=Image.open(FILE)
      st.sidebar.image(image ,caption="Uploaded Image",use_contained_width=True)

      if image.mode in ("RGBA","P"):
           image = image.convert("RGB")

      base_name = os.path.splitext(FILE.name)[0]
      save_path = f"{base_name}.jpg"

      image.save(save_path,"JPEG")
      st.sidebar.success(f" Image Successfully saved as '{save_path}'")
      
   except Exception as e:
      st.error(f"Error processing image:{e}")

profile_url = "https://s7d1.scene7.com/is/image/wbcollab/India_PM_Narendra_Modi-2?qlt=75&resMode=sharp2"

# Change this when required new resume by user, pass details

user_info = st.text_area("Give your information: ")


user_query = f"""user details:given below:
resume info {user_info}
DEFAULT IF NOT GIVEN  : PYTHON DEVELOPER RESUME"""
    
final_query = final_prompt + user_query

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

if st.button("Generate Resume"):
  with st.spinner("Agent creating Resume..."):
    response = agent.invoke({'messages':[{'role':'user',"content":final_query}]})
    code = response['messages'][-1].content[-1]['text']

    if FILE is not None: 
         with open(save_path,"rb") as image_file:
                  b64_image=base64.b64encode(img_file.read()).decode()
         data_uri=f"data:image/jpeg;base64,{b64_image}"
         code=code.replace("PROFIL_IMAGE_PLACEHOLDER",data_uri)

    st.html(code, width="stretch", unsafe_allow_javascript=True)
# =================APPLY LIVE JOBS============
    st.divider()
    response = agent.invoke({'messages':[{'role':'user',"content":job_prompt}]})
    job_code = response['messages'][-1].content[-1]['text']
    st.html(job_code, width="stretch", unsafe_allow_javascript=True)
