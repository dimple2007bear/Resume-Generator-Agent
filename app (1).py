# st.markdown("""## user can create or download resume based on high ATS score """)
# =============================== AGENT CODE ===========================================
import os
import base64
import streamlit as st
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient
from PIL import Image

st.title("AI RESUME MAKER & JOB APPLY AGENT")
st.image(
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrGg1PzVvppycJgP2W8V_0eYflg5xcVNxXXYn3OlOGUP6JDnu9O_SZnks&s=10",
    width=300,
)

# ------------------------- API KEYS -------------------------
GOOGLE = st.sidebar.text_input("GEMINI", type="password")
GROQ = st.sidebar.text_input("GROQ", type="password")
TAVILY = st.sidebar.text_input("TAVILY", type="password")

# require ALL keys, not "all empty" — original bug let the app continue with blank keys
if not GOOGLE or not TAVILY:
    st.sidebar.warning("Please enter your API keys (Gemini + Tavily required).")
    st.stop()
else:
    st.sidebar.success("API keys loaded")

# ------------------------- HELPERS -------------------------
def extract_text(content):
    """
    Safely pull text out of a model response's .content, whatever shape it is.
    ChatGoogleGenerativeAI usually returns a plain string.
    Some providers/agents return a list of content blocks like [{'type': 'text', 'text': ...}].
    The original code assumed the list-of-dicts shape unconditionally, which crashed
    (e.g. response.content[-1]['text'] on a plain string just indexes the last character).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for item in reversed(content):
            if isinstance(item, dict) and "text" in item:
                return item["text"]
            if isinstance(item, str):
                return item
        return str(content)
    return str(content)


@st.cache_resource
def get_model(api_key: str):
    return ChatGoogleGenerativeAI(
        google_api_key=api_key,
        model="gemini-2.0-flash",  # "gemini-3.5-flash-lite" is not a real model name
        temperature=1,
    )


def search_jobs(query: str):
    """Find recent job listings / news for a given search query using Tavily."""
    tavily_client = TavilyClient(api_key=TAVILY)
    return tavily_client.search(query)


@st.cache_resource
def get_agent(_model):
    return create_agent(model=_model, tools=[search_jobs])


model = get_model(GOOGLE)
agent = get_agent(model)

# ------------------------- PROMPT GENERATION (cached, runs once) -------------------------
PROMPT_FILE = "prompt.py"


def generate_base_prompt(model_):
    """
    Ask the model for a detailed HR-style prompt template used later to build resumes.
    Cached in session_state so it doesn't re-run on every Streamlit rerun
    (Streamlit reruns the whole script on every widget interaction).
    """
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r") as f:
            return f.read()

    seed_prompt = """You are a senior HR resume analyzer. Your main task is to write a
detailed prompt template for generating resumes (for students or experienced
professionals) based on personal information they provide. The generated resume
itself must be in HTML format — include that instruction in the prompt you write."""

    try:
        response = model_.invoke(seed_prompt)
        text = extract_text(response.content)
    except Exception as e:
        st.error(f"Failed to generate base prompt: {e}")
        st.stop()

    with open(PROMPT_FILE, "w") as f:
        f.write(text)
    return text


if "base_prompt" not in st.session_state:
    st.session_state.base_prompt = generate_base_prompt(model)

# ------------------------- IMAGE UPLOADER -------------------------
FILE = st.sidebar.file_uploader("Choose an image file", type=["jpg", "jpeg", "png", "webp"])

save_path = None
if FILE is not None:
    try:
        image = Image.open(FILE)
        st.sidebar.image(image, caption="Uploaded Image", use_container_width=True)

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        base_name = os.path.splitext(FILE.name)[0]
        save_path = f"{base_name}.jpg"
        image.save(save_path, "JPEG")
        st.sidebar.success(f"🎉 Image successfully saved as `{save_path}`!")
    except Exception as e:
        st.error(f"Error processing image: {e}")

# ------------------------- RESUME GENERATOR PROMPT -------------------------
RESUME_INSTRUCTIONS = """You are a helpful AI assistant and job resume maker. Your task is
to output an HTML-format resume with a proper, professional design using modern HTML/CSS/JS.
Use a distinctive color scheme, showcase the candidate's skill set, use side margins/tables,
and make heading text (e.g. "Professional Summary") use a gradient effect.

IMPORTANT: wherever the profile photo goes in the resume, output exactly this tag and
nothing else:
<img src="PROFILE_IMAGE_PLACEHOLDER" style="width:100px;height:100px;border-radius:50%;">
Do not draw or generate any other image tag or placeholder circle yourself."""

final_prompt = RESUME_INSTRUCTIONS + st.session_state.base_prompt

USER_INFO = st.text_area("ENTER YOUR INFORMATION")

user_details = f"""User details given below:
resume info: {USER_INFO}
DEFAULT IF NOT GIVEN: PYTHON DEVELOPER RESUME"""

query = final_prompt + user_details

OPTIONS = ["DELHI", "NOIDA", "GURGAON/GURUGRAM", "KANPUR", "LUCKNOW", "BANGLORE", "PUNE"]
LOCATION = st.sidebar.multiselect("SELECT LOCATION:", options=OPTIONS)

JOB_PROFILE = ["PYTHON DEVELOPER", "GEN AI", "FULL-STACK DEVELOPER", "DATA ANALYST"]
PROFILE = st.sidebar.multiselect("SELECT JOB ROLE", options=JOB_PROFILE)

job_prompt = f"""Based on {PROFILE} jobs in {LOCATION}, find the latest job postings using
the search_jobs tool. Try the top 10 results or however many are available, and present
them like a Naukri-style job board with job name, job description, salary, and apply link.
Output must be HTML only, no markdown."""

# ------------------------- GENERATE -------------------------
if st.button("Generate Resume"):
    with st.spinner("Running agent..."):
        try:
            response = agent.invoke({"messages": [{"role": "user", "content": query}]})
            code = extract_text(response["messages"][-1].content)
        except Exception as e:
            st.error(f"Resume generation failed: {e}")
            code = None

        if code:
            if save_path is not None:
                with open(save_path, "rb") as img_file:
                    b64_image = base64.b64encode(img_file.read()).decode()
                data_uri = f"data:image/jpeg;base64,{b64_image}"
                code = code.replace("PROFILE_IMAGE_PLACEHOLDER", data_uri)

            st.html(code)  # st.html() only accepts the HTML body, no width/js kwargs

    # ------------------------- LIVE JOBS -------------------------
    st.divider()
    with st.spinner("Fetching live job listings..."):
        try:
            job_response = agent.invoke({"messages": [{"role": "user", "content": job_prompt}]})
            job_code = extract_text(job_response["messages"][-1].content)
            st.html(job_code)
        except Exception as e:
            st.error(f"Job search failed: {e}")
