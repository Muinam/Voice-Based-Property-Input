# main.py - Updated with formatted bedrooms/bathrooms in JSON (auto-append words)
from stt import SimpleSTT
from tts import SimpleTTS
from extractor import extract_details
from state_manager import PropertyState
import json
import sys

# Initialize TTS (always used)
try:
    tts = SimpleTTS()
except Exception as e:
    print(f"TTS initialization error: {e}")
    sys.exit(1)

# Greeting
tts.speak("Hello Inaam! Let's create your property listing step by step.")
print("Hello Inaam! Let's create your property listing step by step.")

# Ask user for input mode with shortcuts
tts.speak("Do you want to use voice input or text input? Say or type 'v' for voice or 't' for text.")
print("\nDo you want to use voice input or text input? Type 'v' for voice or 't' for text: ")

input_mode_choice = input("> ").strip().lower()

if "v" in input_mode_choice:
    input_mode = "voice"
    print("Voice mode selected. Speak clearly in English.")
    try:
        stt = SimpleSTT()
    except Exception as e:
        print(f"STT initialization error: {e}")
        print("Falling back to text mode.")
        input_mode = "text"
else:
    input_mode = "text"
    print("Text mode selected. Type your answers.")

state = PropertyState()

print("\n=== Guided Conversation Started ===\n")

# Questions list
questions = [
    ("listing_type", "First, is this property for sale or rent? Say or type 's' for sale or 'r' for rent."),
    ("property_type", "What type of property is it? Say or type 'h' for house, 'a' for apartment, 'f' for flat."),
    ("city", "Which city is the property in? Example: Faisalabad or Lahore"),
    ("area", "What is the area or address? Example: Peoples Colony or DHA Phase 6"),
    ("size", "What is the size? Example: 5 marla"),
    ("bedrooms", "How many bedrooms? Just the number."),
    ("bathrooms", "How many bathrooms? Just the number."),
    ("price", "What is the price? In crore, lakh or monthly rent. Example: 1 crore 50 lakh or 50 thousand monthly"),
    ("features", "Any special features? Parking, furnished, corner, gas, park facing, basement, lift, balcony etc. Tell all or say 'none'.")
]

for field, question in questions:
    retries = 0
    while state.data[field] is None or (field == "features" and not state.data[field]) and retries < 3:
        tts.speak(question)
        print(f"\nQuestion: {question}")
        
        if input_mode == "voice":
            user_text = stt.listen()
        else:
            user_text = input("> ").strip().lower()
            print(f"You typed: {user_text}")
        
        # Exit check
        if "exit" in user_text or "stop" in user_text or "quit" in user_text:
            tts.speak("Okay Inaam, stopping the program. Thank you!")
            print("Program stopped by user.")
            sys.exit(0)
        
        extracted = extract_details(user_text, current_field=field)
        state.update_from_dict(extracted)
        
        if state.data[field] is None or (field == "features" and not state.data[field]):
            retries += 1
            if retries < 3:
                tts.speak(f"Sorry, I didn't understand. Please say or type {field.replace('_', ' ')} again.")
                print(f"Sorry, I didn't understand. Please try again.")
            else:
                tts.speak(f"Max tries done for {field}. Skipping or using default.")
                print(f"Max tries done for {field}. Skipping.")
                if field == "features":
                    state.data[field] = []

# Final confirmation with shortcut
tts.speak("Thank you! All details collected. Confirm? Say or type 'y' for yes or 'n' for no.")
print("\nConfirm? Type 'y' for yes or 'n' for no: ")

if input_mode == "voice":
    confirm_text = stt.listen()
else:
    confirm_text = input("> ").strip().lower()

if "y" in confirm_text or "yes" in confirm_text or "okay" in confirm_text:
    size = state.data.get('size', 'N/A')
    prop_type = state.data.get('property_type', 'Property')
    location = state.data.get('location', 'Your Area')
    beds = state.data.get('bedrooms', 'N/A')
    baths = state.data.get('bathrooms', 'N/A')
    price = state.data.get('price', 'N/A')
    list_type = state.data.get('listing_type', 'Sale/Rent')
    features = ', '.join(state.data.get('features', [])) or 'no special features'

    state.data["title"] = f"{size} {prop_type.capitalize()} for {list_type} in {location}"

    state.data["description"] = (
        f"This attractive {prop_type} is located in {location}, offering great value for families or investors. "
        f"With a spacious {size}, it offers {beds} comfortable bedrooms and {baths} modern bathrooms. "
        f"Available for {list_type.lower()} at a reasonable price of {price}, it includes key features like {features}. "
        f"Prime location with easy access to schools, markets, parks, and roads. Ideal for immediate move-in. Contact today!"
    )

    # Format bedrooms and bathrooms with words in JSON
    if state.data["bedrooms"] and state.data["bedrooms"] != 'N/A':
        state.data["bedrooms"] = f"{state.data['bedrooms']} bedrooms"
    if state.data["bathrooms"] and state.data["bathrooms"] != 'N/A':
        state.data["bathrooms"] = f"{state.data['bathrooms']} bathrooms"


    # STRICT JSON OUTPUT ONLY
    print("\n=== FINAL OUTPUT JSON ===\n")
    print(json.dumps(state.data, ensure_ascii=False, indent=2))
    tts.speak("Listing ready! JSON is printed in terminal. Thank you!")
else:
    tts.speak("Okay, let's try again. Restart the program if needed.")
    print("Confirmation denied. Restart if needed.")

print("\n=== Conversation Ended ===\n")