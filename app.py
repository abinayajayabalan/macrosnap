import streamlit as st
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT

st.set_page_config(page_title="MacroSnap", page_icon="🥗", layout="centered")

# Initialize Gemini Client
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client()

# Initialize chat history and user name
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_name" not in st.session_state:
    st.session_state.user_name = "Friend"

# App Header
st.title("🥗 MacroSnap")
st.caption("Your instant calorie & macro decoder")

# Sidebar for configuration and actions
with st.sidebar:
    st.header("Settings")
    user_name_input = st.text_input("Your Name", value=st.session_state.user_name)
    if user_name_input != st.session_state.user_name:
        st.session_state.user_name = user_name_input
        st.rerun()

    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Display welcome message if chat is empty
if not st.session_state.messages:
    welcome_msg = WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.user_name)
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input (text or image)
prompt = st.chat_input("Tell me what you're eating or upload a photo...")
uploaded_file = st.file_uploader("Upload meal photo", type=["jpg", "jpeg", "png"])

if prompt or uploaded_file:
    user_content = []
    if prompt:
        user_content.append(prompt)
    
    image_part = None
    if uploaded_file:
        bytes_data = uploaded_file.getvalue()
        image_part = types.Part.from_bytes(
            data=bytes_data,
            mime_type=uploaded_file.type
        )
        user_content.append(image_part)
        st.image(bytes_data, caption="Uploaded Meal", width=300)

    # Display user message
    display_text = prompt if prompt else "[Uploaded an image of a meal]"
    st.session_state.messages.append({"role": "user", "content": display_text})
    with st.chat_message("user"):
        st.markdown(display_text)

    # Generate response from Gemini
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your meal..."):
            try:
                # Prepare contents for Gemini API
                chat_contents = []
                for msg in st.session_state.messages:
                    chat_contents.append(msg["content"])
                
                if image_part and prompt:
                    contents = [prompt, image_part]
                elif image_part:
                    contents = ["Analyze this meal photo:", image_part]
                else:
                    contents = prompt

                response = st.session_state.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                    ),
                )
                
                assistant_reply = response.text
                st.markdown(assistant_reply)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            except Exception as e:
                error_msg = f"Sorry, an error occurred: {e}"
                st.error(error_msg)