import streamlit as st
from database import (
    create_usertable,
    add_user,
    login_user,
    save_mood,
    save_phq9,
    save_chat,
)
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import random
import google.generativeai as genai
import pandas as pd
import sqlite3
import joblib

# ------------------- SENTIMENT ANALYSIS -------------------
def detect_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)
    compound = score["compound"]

    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"


# ------------------- GEMINI CONFIG -------------------
genai.configure(api_key=st.secrets["api_keys"]["gemini"])
gen_model = genai.GenerativeModel("gemini-2.5-flash")


# ------------------- MOOD SUGGESTIONS (MODIFIED) -------------------
fallback_tasks = {
    "Positive": [
        "Write down three things you are grateful for right now. 🙏",
        "Listen to your favorite upbeat song and dance like nobody's watching! 💃",
        "Plan a fun activity for the weekend to look forward to. 🗓️",
        "Send a message of appreciation to someone who has helped you. 💌",
        "Take a short walk and notice five beautiful things around you. 🌳",
    ],
    "Neutral": [
        "Take a moment to simply breathe deeply. 🧘",
        "Straighten up your desk or living space. 🧹",
        "Write a simple to-do list for tomorrow. 📝",
        "Put your phone away for 15 minutes. 📵",
        "Drink a full glass of water. 💧",
    ],
    "Negative": [
        "Acknowledge how you're feeling without judgment. It's okay. 🫂",
        "Watch a short video of something that always makes you laugh. 😂",
        "Call or text a friend you trust. 📞",
        "Take a warm shower or bath to reset. 🛀",
        "Listen to music that validates your emotions. 🎶",
    ],
}

def get_suggestions(sentiment):

    prompts = {
        "Positive": "Generate 5 very short and fun tasks to do for someone who is feeling great.",
        "Neutral": "Generate 5 simple and calming tasks for someone with a neutral mood.",
        "Negative": "Generate 5 short and helpful tasks for someone who is feeling low. The tasks should be easy to do.",
    }

    st.subheader("Here are some fresh ideas just for you:")
    try:
        response = gen_model.generate_content(prompts.get(sentiment, "Generate 5 helpful tasks."))
        
        tasks = [t.strip() for t in response.text.split('\n') if t.strip()]

        for task in tasks:
            st.markdown(f"• {task}")

    except Exception as e:
        st.error("I'm having trouble connecting to my AI friend. Here are some classic suggestions for now:")
        for task in random.sample(fallback_tasks.get(sentiment, []), 3):
            st.info(f"• {task}")

    if sentiment == "Positive":
        st.balloons()
        st.success("You're glowing today! 🌟 Keep it up.")
        with st.expander("💬 Talk more about your good day?"):
            st.text_area("Share more!")
            
    elif sentiment == "Neutral":
        st.info("Sometimes okay is just okay and that’s fine. 🌤️")
        st.markdown("Try this quick gratitude note:")
        st.text_area("🙏 I'm thankful for...")

    elif sentiment == "Negative":
        st.error("It's okay to feel low 😔 You're not alone.")
        st.video("https://youtube.com/shorts/zYpdaEIrPlQ?si=KMz4LVbyY74UJlKG")
        st.subheader("This one is for you")
        st.video("https://youtu.be/_1OfB3DGwpA?si=SwERzTsmIiPdyG4n")

        st.subheader("💡 What would you like to do now?")
        col1, col2 = st.columns(2)

        with col1:
            choice = st.radio(
                "Pick a feel-good action:",
                (
                    "🎵 Listen to a Mood-Based Playlist",
                    "✍️ Write a Private Journal Entry",
                    "😂 Laugh Break (Meme/Video)",
                    "📚 Get a Uplift Tip",
                    "🎯 Mini Task Generator",
                ),
            )

        with col2:
            if choice == "🎵 Listen to a Mood-Based Playlist":
                st.markdown("#### 🎧 Here's something to lift you up:")
                st.video("https://www.youtube.com/watch?v=jfKfPfyJRdk")
            elif choice == "✍️ Write a Private Journal Entry":
                st.markdown("#### ✍️ Let it out — it’s safe here.")
                journal_text = st.text_area("What’s on your mind?")
                if st.button("Save Entry"):
                    st.success("Your thoughts are saved privately 🗒️")
            elif choice == "😂 Laugh Break (Meme/Video)":
                st.markdown("#### 😂 Here's something to make you smile:")
                st.image(
                    "https://i.programmerhumor.io/2022/07/programmerhumor-io-programming-memes-49973fb83da3327.jpg",
                    caption="CS students be like 💻",
                )
                st.markdown("This will surely help you😂😂")
                st.video("https://youtu.be/LQlcWclgRlc?si=lxBM7u3WSmCyY9Xq")
            elif choice == "📚 Get a Uplift Tip":
                tips = [
                    "Breathe. You’ve survived 100% of your worst days.",
                    "Grades don’t define your worth.",
                    "Take breaks — not breakdowns.",
                    "It’s okay to rest. Hustle is not everything.",
                    "Talk to someone. Even a journal helps.",
                ]
                st.success(random.choice(tips))
            elif choice == "🎯 Mini Task Generator":
                task = random.choice(
                    [
                        "Take a 3-minute stretch break 🧘",
                        "Drink a full glass of water 💧",
                        "Send a funny meme to a friend 💬",
                        "Go touch grass 🌿 (seriously)",
                        "Write 3 things you’re grateful for 🙏",
                    ]
                )
                st.info(task)


# ------------------- GEMINI CHAT -------------------
def gemini_chat_ui():
    st.subheader("Feel free to chat with your AI friend!")
    st.markdown("##### _Type something to talk..._")

    if "chat" not in st.session_state:
        st.session_state.chat = gen_model.start_chat(history=[])

    user_msg = st.text_input("You: ", key="chat_input")

    if st.button("Send"):
        if user_msg.strip() != "":
            try:
                response = st.session_state.chat.send_message(user_msg)
                st.markdown("**AI says:**")
                st.info(response.text)

                if response:
                    save_chat(st.session_state["username"], user_msg, response.text)

            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please type a message.")


# ------------------- CHAT HISTORY -------------------
def view_chat_history():
    st.subheader(" Your Chat History")
    if "username" in st.session_state:
        username = st.session_state["username"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message,response,timestamp FROM chat_history WHERE username = ? ORDER BY timestamp DESC",
            (username,),
        )
        records = cursor.fetchall()
        conn.close()

        if records:
            for i, (message, response, timestamp) in enumerate(records, 1):
                with st.expander(f" {timestamp}"):
                    st.markdown(f"**You:** {message}")
                    st.markdown(f"**AI:** {response}")
        else:
            st.info("No chat history found.")
    else:
        st.warning("Please log in or identify yourself first.")


# ------------------- PHQ-9 MODEL -------------------
model = joblib.load("phq9_model.pkl")


def show_suggestions(level):
    st.markdown("### 🩺 Suggested Support Based on Your Mood:")

    if level == "None":
        st.success("You're doing well. Keep maintaining your routine. ✅")
        st.markdown("- Continue your healthy habits 🌿")
        st.markdown("- Stay socially connected 💬")
        st.markdown("- Practice gratitude daily 🙏")

    elif level == "Mild":
        st.info("You're showing mild signs of low mood. Let's care for your mind. 💡")
        st.markdown("- Try 10-minute journaling ✍️")
        st.markdown("- Take a mindful walk 🧘‍♂️")
        st.markdown("- Listen to calming music 🎵")

    elif level == "Moderate":
        st.warning("You may be experiencing moderate symptoms of depression.")
        st.markdown("- Reach out to a trusted friend or mentor ☎️")
        st.markdown("- Follow a consistent sleep schedule 🛌")
        st.markdown("- Try guided meditation")

    elif level == "Moderately Severe":
        st.error("Your responses indicate a need for support.")
        st.markdown("- Please consider talking to a counselor or therapist 🎓")
        st.markdown("- Limit negative screen time 📵")
        st.markdown("- Follow a self-care checklist daily 📋")

    elif level == "Severe":
        st.error("⚠️ Your mental health needs urgent care.")
        st.markdown(
            "**It’s highly recommended that you seek professional help immediately.**"
        )
        st.markdown("- Visit a mental health professional 👩‍⚕️")
        st.markdown("- Talk to someone you trust ❤️")
        st.markdown("- You are not alone — help is available. 💌")


def phq9_form():
    st.subheader("PHQ-9 Depression Screening")

    questions = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself — or that you are a failure",
        "Trouble concentrating on things",
        "Moving or speaking slowly or being fidgety/restless",
        "Thoughts that you would be better off dead",
    ]

    options = {
        "Not at all": 0,
        "Several days": 1,
        "More than half the days": 2,
        "Nearly every day": 3,
    }

    answers = []
    for q in questions:
        ans = st.radio(q, list(options.keys()), key=q)
        answers.append(options[ans])

    if st.button("Submit Screening"):
        total_score = sum(answers)
        prediction = model.predict([answers])

        st.success(f"Total PHQ-9 Score: {total_score}")
        st.info(f"Predicted Depression Level: {prediction}")

        show_suggestions(prediction)
        save_phq9(st.session_state["username"], total_score, prediction[0])

        st.subheader(
            ".....Please go to 'AI FRIEND' section in sidebar you will love it......."
        )


# ------------------- MAIN APP -------------------
create_usertable()
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Montserrat:wght@900&display=swap');

        /* ----------- GLOBAL DARK THEME ----------- */
        body, .main, .stApp {
            background: linear-gradient(135deg, #0F0C29, #302B63, #24243E) !important;
            color: #EAEAEA !important;
        }

        /* Make all Streamlit containers dark */
        .block-container {
            background: transparent !important;
        }

        /* ----------- TITLE ----------- */
        .main-title {
            font-family: 'Pacifico', cursive;
            font-size: 72px;
            font-weight: 900;
            text-align: center;
            letter-spacing: 2px;
            background: -webkit-linear-gradient(45deg, #A56CFF, #FF8AD4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: 20px;
            margin-bottom: 40px;
        }

        /* ----------- INPUT FIELDS ----------- */
        .stTextInput>div>div>input {
            background-color: #1F1B3A !important;
            color: white !important;
            border-radius: 10px !important;
            border: 1px solid #8A2BE2 !important;
        }

        .stTextInput>div>div>input:focus {
            border: 1.5px solid #FF69B4 !important;
            background-color: #2A224A !important;
        }

        /* ----------- BUTTONS ----------- */
        .stButton>button {
            border-radius: 20px;
            border: 2px solid #FF69B4;
            color: white;
            background: linear-gradient(135deg, #5A0EA1, #8A2BE2);
            transition: all 0.3s ease-in-out;
            padding: 10px 20px;
            font-weight: 600;
        }

        .stButton>button:hover {
            background: linear-gradient(135deg, #FF69B4, #A020F0);
            color: white;
            border: 2px solid #FFFFFF;
            transform: translateY(-2px);
            box-shadow: 0px 4px 15px rgba(255, 105, 180, 0.25);
        }

        /* ----------- TABS ----------- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 20px 20px 0 0 !important;
            background-color: #5A0EA1;
            color: white;
            padding: 10px 20px;
            transition: all 0.3s ease-in-out;
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            background-color: #FF69B4 !important;
            color: #2A004D !important;
            box-shadow: 0px -3px 10px rgba(255, 105, 180, 0.4);
        }

        /* ----------- LABELS / HEADINGS ----------- */
        h1, h2, h3, h4, h5, label, p {
            color: #EAEAEA !important;
        }
    </style>

    <div class="main-title">MIND MATE</div>
    """,
    unsafe_allow_html=True,
)

# ------------------- LOGIN/SIGNUP UI -------------------
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_tab, signup_tab = st.tabs(["🔐 Login", "➕ Sign Up"])

    with login_tab:
        st.subheader("Login to your account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            result = login_user(username, password)
            if result:
                st.success(f"Welcome back, {username}!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["submitted"] = False
                st.rerun()
            else:
                st.error("Invalid credentials")

    with signup_tab:
        st.subheader("Create New Account")
        new_user = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            add_user(new_user, new_password)
            st.success("Account created! 🎉 Now you can Login.")

# ------------------- LOGGED-IN PAGES -------------------
else:
    # A single row for tabs and a logout button
    tab_list, logout_col = st.columns([5,1])
    with tab_list:
        st.subheader(f"Welcome, {st.session_state['username']}!")
    with logout_col:
        if st.button("Logout"):
            st.session_state.clear()
            st.success("You have been logged out. 👋")
            st.rerun()

    # Tabs for main navigation
    tab1, tab2, tab3, tab4 = st.tabs(["Home", "AI Friend", "Screening", "Chat History"])

    # ------------------- TAB 1: HOME -------------------
    with tab1:
        if "submitted" not in st.session_state:
            st.session_state["submitted"] = False

        if not st.session_state["submitted"]:
            st.markdown("### Tell me about your day. I'm here to listen... 💬")
            user_input = st.text_area("How was your day today?", height=150)

            if st.button("Submit Mood"):
                if user_input:
                    sentiment = detect_sentiment(user_input)
                    st.session_state["sentiment"] = sentiment
                    st.session_state["submitted"] = True
                    save_mood(st.session_state["username"], sentiment, user_input)
                    st.rerun()
                else:
                    st.warning("Please share something about your day.")
        else:
            sentiment = st.session_state.get("sentiment", "Neutral")
            st.success(f"Detected Mood: {sentiment} ")
            get_suggestions(sentiment)

            if st.button("🔄 Start Over"):
                st.session_state["submitted"] = False
                st.rerun()
    
    # ------------------- TAB 2: GEMINI CHAT -------------------
    with tab2:
        gemini_chat_ui()

    # ------------------- TAB 3: DEPRESSION SCREENING -------------------
    with tab3:
        phq9_form()
    
    # ------------------- TAB 4: CHAT HISTORY -------------------
    with tab4:
        view_chat_history()