import streamlit as st
from stt import SimpleSTT
from tts import SimpleTTS
from extractor import extract_details, post_process_field
from state_manager import PropertyState
import json
import os
import time
import zipfile
import io
from PIL import Image
import random

# ────────────────────────────────────────────────
# Page Configuration – Professional UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="Property Listing Generator", page_icon="🏠", layout="wide")

st.markdown("""
    <style>
    .main { padding: 2rem; background: #f9fafb; }
    .stButton > button { width: 100%; height: 3rem; font-size: 1.1rem; border-radius: 10px; }
    .stButton > button[kind="primary"] { background: #2563eb; color: white; }
    h1, h2 { color: #1e40af; }
    .question-card { background: white; padding: 1.8rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin: 1.5rem 0; }
    .info-box { background: #eff6ff; padding: 1rem; border-radius: 10px; margin: 1rem 0; }
    hr { margin: 2.5rem 0; border-color: #e5e7eb; }
    </style>
""", unsafe_allow_html=True)

st.title("🏠 Property Listing Generator")
st.markdown("Create professional property listings effortlessly using voice or text.")

# ────────────────────────────────────────────────
# Session State
# ────────────────────────────────────────────────
if 'state' not in st.session_state:
    st.session_state.state = PropertyState()
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'input_mode' not in st.session_state:
    st.session_state.input_mode = 'text'
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'tts_played_for_step' not in st.session_state:
    st.session_state.tts_played_for_step = -1
if 'final_audio_file' not in st.session_state:
    st.session_state.final_audio_file = None
if 'final_tts_played' not in st.session_state:
    st.session_state.final_tts_played = False
if 'last_audio_cleanup' not in st.session_state:
    st.session_state.last_audio_cleanup = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'missing_fields' not in st.session_state:
    st.session_state.missing_fields = []
if 'confirmation_done' not in st.session_state:
    st.session_state.confirmation_done = False

# Image upload storage
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []
if 'images_preview' not in st.session_state:
    st.session_state.images_preview = []

# ────────────────────────────────────────────────
# Load Models
# ────────────────────────────────────────────────
@st.cache_resource
def get_tts():
    return SimpleTTS()

@st.cache_resource
def get_stt():
    return SimpleSTT()

tts = get_tts()
stt_obj = get_stt()

# ────────────────────────────────────────────────
# Questions
# ────────────────────────────────────────────────
questions = [
    ("listing_type", "Is this property for sale or rent?"),
    ("property_type", "What type of property is it?"),
    ("city", "Which city is the property in?"),
    ("area", "What is the area or society name?"),
    ("size", "What is the size of the property?"),
    ("bedrooms", "How many bedrooms does it have?"),
    ("bathrooms", "How many bathrooms?"),
    ("price", "What is the asking price?"),
    ("features", "What are the key features?")
]

# ────────────────────────────────────────────────
# Sidebar
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")
    mode = st.radio("Input Mode", ["Text", "Voice"], horizontal=True)
    st.session_state.input_mode = "voice" if mode == "Voice" else "text"

    if st.session_state.input_mode == "voice":
        st.info("Speak clearly — questions will be spoken automatically.")

# ────────────────────────────────────────────────
# Greeting (only once)
# ────────────────────────────────────────────────
if st.session_state.step == 0 and not st.session_state.conversation_history:
    greeting = random.choice([
        "Hello! Let's create a beautiful listing for your property.",
        "Hi there! I'm here to help you make a perfect property ad.",
        "Welcome! Ready to list your property? Let's get started."
    ])
    st.session_state.conversation_history.append(("AI", greeting))
    if st.session_state.input_mode == "voice":
        audio = tts.speak_to_file(greeting)
        if audio:
            st.audio(audio, format='audio/wav', autoplay=True)
            time.sleep(0.3)
            os.remove(audio)

# ────────────────────────────────────────────────
# Main Questions Flow
# ────────────────────────────────────────────────
if st.session_state.step < len(questions) and not st.session_state.confirmation_done:
    field, base_question = questions[st.session_state.step]

    friendly_questions = {
        "listing_type": ["First, is this property for sale or rent?"],
        "property_type": ["What kind of property is it?"],
        "city": ["Which city is this property located in?"],
        "area": ["Which area or society is it in?"],
        "size": ["What's the size of the property?"],
        "bedrooms": ["How many bedrooms are there?"],
        "bathrooms": ["And bathrooms?"],
        "price": ["What's the asking price?"],
        "features": ["Any special features you'd like to mention?"]
    }
    question = random.choice(friendly_questions.get(field, [base_question]))

    with st.container():
        st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
        st.subheader(f"Step {st.session_state.step + 1} of {len(questions)}")
        st.markdown(f"**{question}**")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.input_mode == "voice":
        if st.session_state.tts_played_for_step != st.session_state.step:
            with st.spinner("Speaking..."):
                audio_file = tts.speak_to_file(question)
                if audio_file:
                    st.audio(audio_file, format='audio/wav', autoplay=True)
                    if st.session_state.last_audio_cleanup:
                        try: os.remove(st.session_state.last_audio_cleanup)
                        except: pass
                    st.session_state.last_audio_cleanup = audio_file
            st.session_state.tts_played_for_step = st.session_state.step

    # Input section
    if st.session_state.input_mode == "voice":
        if st.button("🎤 Speak Answer", type="primary"):
            with st.spinner("Listening..."):
                try:
                    spoken = stt_obj.listen(max_duration=25, silence_timeout=2.5)
                    st.session_state.user_text = spoken.strip()
                    if st.session_state.user_text:
                        st.success(f"You said: **{st.session_state.user_text}**")
                    else:
                        st.warning("Didn't catch that. Please speak again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.session_state.user_text = st.text_input("Your answer:", key=f"q_{st.session_state.step}")

    if st.button("Submit", type="primary"):
        user_text = st.session_state.user_text.strip()
        if not user_text:
            st.warning("Please provide an answer.")
        else:
            first = user_text[0].lower() if user_text else ""
            if field == "listing_type":
                if first == 's': user_text = "sale"
                elif first == 'r': user_text = "rent"
            elif field == "property_type":
                if first == 'h': user_text = "house"
                elif first == 'a': user_text = "apartment"
                elif first == 'f': user_text = "flat"

            extracted = extract_details(user_text, current_field=field)
            for f, v in list(extracted.items()):
                if v and f in ["price", "size", "city", "area", "features"]:
                    extracted[f] = post_process_field(f, v)

            st.session_state.state.update_from_dict(extracted)

            if st.session_state.state.data.get(field) is not None:
                st.success(f"Saved: **{field}** = {st.session_state.state.data[field]}")
                st.session_state.step += 1
                st.session_state.user_text = ""
                st.rerun()
            else:
                st.warning("Could not understand. Try again.")

# ────────────────────────────────────────────────
# Follow-up for missing fields
# ────────────────────────────────────────────────
elif st.session_state.step >= len(questions) and not st.session_state.confirmation_done:
    required = ["listing_type", "property_type", "city", "area", "size", "bedrooms", "bathrooms", "price"]
    missing = [q[0] for q in questions if q[0] not in st.session_state.state.data or not st.session_state.state.data[q[0]] or st.session_state.state.data[q[0]] == "N/A"]

    if missing:
        next_missing = missing[0]
        follow_up_map = {
            "listing_type": "Just to confirm — is this for sale or rent?",
            "property_type": "What type of property is it? House, apartment, flat?",
            "city": "Which city is the property located in?",
            "area": "Which area or society?",
            "size": "What's the size? Marla, kanal, or square feet?",
            "bedrooms": "How many bedrooms?",
            "bathrooms": "And bathrooms?",
            "price": "What's the asking price?"
        }
        question = follow_up_map.get(next_missing, f"Please tell me about {next_missing.replace('_', ' ')}.")

        with st.container():
            st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
            st.subheader("One more thing...")
            st.markdown(f"**{question}**")
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.input_mode == "voice":
            audio = tts.speak_to_file(question)
            if audio:
                st.audio(audio, format='audio/wav', autoplay=True)
                time.sleep(0.3)
                os.remove(audio)

        if st.session_state.input_mode == "voice":
            if st.button("🎤 Speak Now"):
                with st.spinner("Listening..."):
                    try:
                        spoken = stt_obj.listen(max_duration=25, silence_timeout=2.5)
                        st.session_state.user_text = spoken.strip()
                        if st.session_state.user_text:
                            st.success(f"You said: **{st.session_state.user_text}**")
                    except:
                        st.error("Couldn't hear clearly. Try again.")
        else:
            st.session_state.user_text = st.text_input("Your answer:")

        if st.button("Submit"):
            user_text = st.session_state.user_text.strip()
            extracted = extract_details(user_text, current_field=next_missing)
            for f, v in extracted.items():
                if v:
                    st.session_state.state.data[f] = v
            st.session_state.user_text = ""
            st.rerun()

    else:
        st.session_state.confirmation_done = True
        st.rerun()

# ────────────────────────────────────────────────
# Confirmation Step
# ────────────────────────────────────────────────
elif st.session_state.confirmation_done and not st.session_state.get('final_output_shown', False):
    st.subheader("Please Confirm the Details")

    data = st.session_state.state.data
    summary = f"""
    **Property Type:** {data.get('property_type', 'N/A')}  
    **Location:** {data.get('location', 'N/A')}  
    **Size:** {data.get('size', 'N/A')}  
    **Bedrooms:** {data.get('bedrooms', 'N/A')}  
    **Bathrooms:** {data.get('bathrooms', 'N/A')}  
    **Price:** {data.get('price', 'N/A')}  
    **Listing Type:** {data.get('listing_type', 'N/A')}  
    **Features:** {', '.join(data.get('features', [])) or 'None'}
    """

    st.markdown(summary)

    confirm_text = "Are these details correct? Say or type 'yes' to finalize, or 'no' to make changes."
    st.markdown(f"**{confirm_text}**")

    # NEW: TTS sirf ek baar bajega (confirmation screen pe pehli baar)
    if not st.session_state.get('confirmation_tts_played', False):
        if st.session_state.input_mode == "voice":
            audio = tts.speak_to_file(confirm_text)
            if audio:
                st.audio(audio, format='audio/wav', autoplay=True)
                time.sleep(0.3)
                os.remove(audio)
        st.session_state.confirmation_tts_played = True

    # Input section – TTS ab dobara nahi chalega
    if st.session_state.input_mode == "voice":
        if st.button("🎤 Speak Yes or No"):
            with st.spinner("Listening..."):
                try:
                    spoken = stt_obj.listen(max_duration=10, silence_timeout=1.8)
                    st.session_state.user_text = spoken.strip().lower()
                    if st.session_state.user_text:
                        st.success(f"You said: **{st.session_state.user_text}**")
                except:
                    st.error("Couldn't hear. Try again.")
    else:
        st.session_state.user_text = st.text_input("Yes or No:")

    if st.button("Submit Confirmation"):
        answer = st.session_state.user_text.strip().lower()
        if "yes" in answer or "y" in answer or "okay" in answer or "ok" in answer:
            st.session_state.final_output_shown = True
            st.rerun()
        else:
            st.warning("Okay, let's go back and fix any details.")
            st.session_state.confirmation_done = False
            st.session_state.confirmation_tts_played = False  # Reset TTS flag agar wapas aaye
            st.session_state.step = 0
            st.rerun()

# ────────────────────────────────────────────────
# Final JSON Output – STRICT JSON ONLY
# ────────────────────────────────────────────────
elif st.session_state.get('final_output_shown', False):
    data = st.session_state.state.data

    required = ["listing_type", "property_type", "city", "area", "size", "bedrooms", "bathrooms", "price", "features"]
    for f in required:
        if f not in data or not data[f]:
            data[f] = "N/A" if f != "features" else []

    city = data.get("city", "")
    area = data.get("area", "")
    location = f"{area}, {city}".strip() if area and city else city or area or "N/A"

    size = data.get("size", "N/A")
    prop_type = data.get("property_type", "Property").capitalize()
    beds = data.get("bedrooms", "N/A")
    baths = data.get("bathrooms", "N/A")
    price = data.get("price", "N/A")
    list_type = data.get("listing_type", "Sale/Rent")
    features_list = data.get("features", [])
    features = ', '.join(features_list) if features_list else 'no special features'

    data["title"] = f"{size} {prop_type} for {list_type} in {location}"
    data["description"] = (
        f"This attractive {prop_type} is located in {location}, offering great value for families or investors. "
        f"With a spacious {size}, it offers {beds} comfortable bedrooms and {baths} modern bathrooms. "
        f"Available for {list_type.lower()} at a reasonable price of {price}, it includes key features like {features}. "
        f"Prime location with easy access to schools, markets, parks, and roads. Ideal for immediate move-in. Contact today!"
    )

    if beds != "N/A":
        data["bedrooms"] = f"{beds} bedrooms"
    if baths != "N/A":
        data["bathrooms"] = f"{baths} bathrooms"

    # STRICT JSON OUTPUT – no extra text
    final_json = {
        "title": data["title"],
        "description": data["description"],
        "property_type": prop_type,
        "location": location,
        "bedrooms": data.get("bedrooms", "N/A"),
        "bathrooms": data.get("bathrooms", "N/A"),
        "size": size,
        "price": price,
        "listing_type": list_type,
        "features": features_list
    }

    st.json(final_json)

    # Final TTS – auto play
    if st.session_state.final_audio_file is None:
        final_text = f"Your listing is ready. {data['title']}. {data['description']}"
        audio_file = tts.speak_to_file(final_text)
        if audio_file:
            st.session_state.final_audio_file = audio_file

    if st.session_state.final_audio_file and os.path.exists(st.session_state.final_audio_file):
        if not st.session_state.final_tts_played:
            st.audio(st.session_state.final_audio_file, format='audio/wav', autoplay=True)
            st.session_state.final_tts_played = True

        if st.button("🔊 Listen to Full Description"):
            st.audio(st.session_state.final_audio_file)

    # Download JSON
    st.download_button(
        "Download Final JSON",
        json.dumps(final_json, ensure_ascii=False, indent=2),
        file_name="property_listing.json",
        mime="application/json"
    )

    # Start Over
    if st.button("Start New Listing", type="primary"):
        if st.session_state.final_audio_file and os.path.exists(st.session_state.final_audio_file):
            os.remove(st.session_state.final_audio_file)
        if st.session_state.last_audio_cleanup and os.path.exists(st.session_state.last_audio_cleanup):
            os.remove(st.session_state.last_audio_cleanup)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()