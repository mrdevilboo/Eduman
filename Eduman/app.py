import streamlit as st
import time
import base64
from PIL import Image
import io
import google.generativeai as genai
import random
import json

# --------------------------------------------
# SAFE BASE64 IMAGE LOADER
# --------------------------------------------
def load_image_base64(path):
    try:
        img = Image.open(path)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        return base64.b64encode(byte_im).decode()
    except Exception:
        return None

ICON_PATH = "Eduman/assets/home_background.png"
HOME_BG = "Eduman/assets/home_background.png"

icon_base64 = load_image_base64(ICON_PATH)
home_bg_base64 = load_image_base64(HOME_BG)

# PAGE CONFIG
st.set_page_config(page_title="EduMan", layout="centered")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# --------------------------------------------
# Apply Background Globally
# --------------------------------------------
def apply_global_background():
    if home_bg_base64:
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{home_bg_base64}");
                    background-size: cover;
                    background-position: center;
                }}
                .stButton > button {{
                    background-color: #007BFF !important;
                    color: white !important;
                    padding: 12px 36px !important;
                    font-size: 20px !important;
                    font-weight: 600 !important;
                    border-radius: 8px !important;
                    margin: 6px 0 !important;
                }}
                .question-box {{
                    background: rgba(0,0,0,0.0); /* No white box */
                    color: white;
                    padding: 16px;
                    font-size: 26px;
                    text-align:center;
                    font-weight:600;
                }}
                label {{
                    color:white !important;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

# --------------------------------------------
# LOADING SCREEN
# --------------------------------------------
def loading_screen():
    image_html = (
        f'<img class="em-logo" src="data:image/png;base64,{icon_base64}" />'
        if icon_base64 else "Logo Missing"
    )
    st.markdown(
        f"""
        <style>
            html, body, .stApp {{
                background: white !important;
            }}
            .center-screen {{
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                transform: translateY(-60px);
            }}
            .inner {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 24px;
            }}
            .em-logo {{
                width: 115px;
                border-radius: 14px;
            }}
            .title-text {{
                font-size: 42px;
                font-weight: 700;
                color: black;
            }}
            .loader {{
                width: 280px;
                height: 12px;
                background: #e5e7eb;
                border-radius: 10px;
                overflow: hidden;
                position: relative;
            }}
            .loader::before {{
                content: "";
                position: absolute;
                height: 100%;
                width: 0%;
                background: #347cff;
                animation: loadAnim 2.2s linear forwards;
            }}
            @keyframes loadAnim {{
                from {{ width: 0%; }}
                to {{ width: 100%; }}
            }}
        </style>
        <div class="center-screen">
            <div class="inner">
                {image_html}
                <div class="title-text">Loading EduMan</div>
                <div class="loader"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(2.2)
    st.session_state["screen"] = "home"
    st.rerun()

# --------------------------------------------
# HOME SCREEN
# --------------------------------------------
def home_screen():
    apply_global_background()
    st.markdown(
        """
        <div style="text-align:center; margin-top:120px;">
            <h1 style="color:white; font-size:60px; font-weight:800;">
                🎮 EduMan
            </h1>
            <div style="color:white; font-size:30px; margin-top:-10px;">
                An AI Powered Educational Game
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([4,2,4])
    with col2:
        start = st.button("Start Game")
        if start:
            st.session_state["screen"] = "game_selector"
            st.rerun()

# --------------------------------------------
# GAME SELECTOR
# --------------------------------------------
def game_selector_screen():
    apply_global_background()

    st.markdown(
        "<div style='text-align:center; font-size:45px; font-weight:800; color:white; margin-top:120px;'>🎮 Game Selector</div>",
        unsafe_allow_html=True
    )

    selected_class = st.selectbox("Class", ["5th","6th","7th","8th","9th","10th","11th","12th"])
    board = st.selectbox("Board", ["CBSE", "CISCE", "NIOS", "State Board", "Other"])
    other_board = st.text_input("Enter Board Name") if board == "Other" else board

    subject = st.selectbox("Subject", ["Maths", "Science", "Social", "English"])
    lesson = st.text_input("Lesson (Optional)")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

    if st.button("Begin Game"):
        st.session_state["game_inputs"] = {
            "class": selected_class,
            "board": other_board,
            "subject": subject,
            "lesson": lesson,
            "difficulty": difficulty,
        }
        st.session_state["screen"] = "game_page"
        st.session_state["qno"] = 1
        st.session_state["answer_state"] = "waiting"

        if "current_question" in st.session_state:
            del st.session_state["current_question"]

        st.rerun()

# --------------------------------------------
# SAFE JSON EXTRACTOR (NO REGEX RECURSION)
# --------------------------------------------
def safe_json_from_text(text: str):
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None

    json_str = text[start:end+1]

    try:
        return json.loads(json_str)
    except:
        return None

# --------------------------------------------
# QUESTION GENERATOR
# --------------------------------------------
def generate_question(inputs):

    # Stronger randomness so Gemini NEVER repeats
    seed = random.randint(1000000, 9999999)
    noise = random.choice([
        "make it funny",
        "make it tricky",
        "avoid previously seen patterns",
        "use uncommon numbers",
        "use real-life scenario",
        "use classroom example"
    ])

    prompt = f"""
    Generate a UNIQUE multiple-choice question. 
    Never repeat earlier questions. Add creativity: {noise}
    
    SEED: {seed}

    Output strictly JSON only:
    {{
      "question": "<text>",
      "options": ["A) ...","B) ...","C) ...","D) ..."],
      "answer": "A/B/C/D"
    }}

    Class: {inputs['class']}
    Board: {inputs['board']}
    Subject: {inputs['subject']}
    Lesson: {inputs['lesson']}
    Difficulty: {inputs['difficulty']}
    """

    # Add temperature for more variety
    res = model.generate_content(
        prompt,
        generation_config={"temperature": 0.9}
    )

    parsed = safe_json_from_text(res.text)

    if parsed:
        return parsed

    # Fallback (only if model fails)
    return {
        "question": "Fallback: What is 5 × 3?",
        "options": ["A) 8", "B) 15", "C) 10", "D) 35"],
        "answer": "B"
    }


# --------------------------------------------
# GAME PAGE
# --------------------------------------------
def game_page():
    apply_global_background()

    inputs = st.session_state["game_inputs"]

    timer_map = {"Easy": 60, "Medium": 45, "Hard": 30}
    duration = timer_map[inputs["difficulty"]]

    if "current_question" not in st.session_state:
        st.session_state["current_question"] = generate_question(inputs)
        st.session_state["start_time"] = time.time()

    q = st.session_state["current_question"]

    st.markdown(
        f"<h1 style='color:white; text-align:center;'>🧠 Question {st.session_state['qno']}</h1>",
        unsafe_allow_html=True
    )

    elapsed = int(time.time() - st.session_state["start_time"])
    remaining = max(duration - elapsed, 0)

    st.markdown(
        f"<h2 style='text-align:center; color:white;'>⏳ Time Left: {remaining} sec</h2>",
        unsafe_allow_html=True
    )

    if remaining == 0 and st.session_state["answer_state"] == "waiting":
        st.session_state["answer_state"] = "timeout"

    st.markdown(
        f"<div class='question-box'>{q['question']}</div>",
        unsafe_allow_html=True
    )

    choice = st.radio("Choose your answer:", q["options"], index=None)

    if st.button("Submit") and st.session_state["answer_state"] == "waiting":
        if choice:
            picked = choice[0]
            st.session_state["answer_state"] = "correct" if picked == q["answer"] else "wrong"
        else:
            st.warning("Please choose an option.")

    if st.session_state["answer_state"] == "correct":
        st.success("✔ Correct!")
    elif st.session_state["answer_state"] == "wrong":
        st.error(f"❌ Wrong! Correct Answer: {q['answer']}")
    elif st.session_state["answer_state"] == "timeout":
        st.error(f"⏳ Time's up! Correct Answer: {q['answer']}")

    if st.session_state["answer_state"] != "waiting":

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Next Question"):
                st.session_state["qno"] += 1
                st.session_state["current_question"] = generate_question(inputs)
                st.session_state["answer_state"] = "waiting"
                st.session_state["start_time"] = time.time()
                st.rerun()

        with c2:
            if st.button("Go To Home"):
                st.session_state["screen"] = "home"
                st.rerun()

# --------------------------------------------
# ROUTER
# --------------------------------------------
if "screen" not in st.session_state:
    st.session_state["screen"] = "loading"

if st.session_state["screen"] == "loading":
    loading_screen()
elif st.session_state["screen"] == "home":
    home_screen()
elif st.session_state["screen"] == "game_selector":
    game_selector_screen()
elif st.session_state["screen"] == "game_page":
    game_page()



