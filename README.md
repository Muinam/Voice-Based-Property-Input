# Voice-Based Property Input Data Collection (JSON Output)
Overview

This project is a voice-interactive property listing system that collects real estate information step-by-step and generates structured JSON output.

It supports:

🎤 Voice Input (Speech-to-Text)

⌨️ Text Input Mode

🔊 Text-to-Speech Responses

🧠 Smart Data Extraction

📄 Auto-Generated Title & Description

📦 Clean JSON Output

## How It Works

System greets the user.

User selects:

v → Voice Mode

t → Text Mode

Guided questions collect:

Listing type (sale/rent)

Property type

City

Area

Size

Bedrooms

Bathrooms

Price

Features

System confirms details.

Final structured JSON is printed in terminal.

## Technologies Used

Faster-Whisper (tiny.en) → Speech-to-Text

facebook/mms-tts-eng → Text-to-Speech

Python

JSON formatting


Custom state management system
