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
import tempfile

# =========================FRONTEND==================
st.title("AI RESUME GENERATOR")

GOOGLE_API_KEY = st.sidebar.text_input("Google Api Key", type = 'password')
GROQ_API_KEY = st.sidebar.text_input("GROQ Api Key", type = 'password')
TAVILY_API_KEY = st.sidebar.text_input("TAVILY Api Key", type = 'password')

if not GOOGLE_API_KEY:
  st.warning("Provide Google API key")


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
    api_key = GROQ_API_KEY
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



prompt = """I want complete Professional
Resume with Dynamic Design using Advanced CSS and JS
and must show user input details
System instructions: Only Give HTML code as output"""

final_prompt = prompt + prompt_reader()

profile_url = "https://s7d1.scene7.com/is/image/wbcollab/India_PM_Narendra_Modi-2?qlt=75&resMode=sharp2"

# Change this when required new resume by user, pass details

user_info = st.text_input("Give your information: ")
user_photo = st.sidebar.file_uploader("Upload pic", type = 'image/jpeg')

if user_photo is not None:
  # Create a temporary file
  with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
    tmp.write(user_photo.getvalue())
    tmp_path = tmp.name

user_query = f"""Give Resume for Python Developer.
    user details : {user_info}
    use user profile image from given {tmp_path}"""

final_query = final_prompt + user_query

if st.button("Generate Resume"):
  with st.spinner("Agent creating Resume..."):
    response = agent.invoke({'messages':[{'role':'user',"content":final_query}]})
    code = response['messages'][-1].content[-1]['text']
    
    st.html(code, width="stretch", unsafe_allow_javascript=True)




