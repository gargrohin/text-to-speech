import os
import requests
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    Response,
    stream_with_context,
)

# --- Configuration ---
# You can set defaults here, but we'll primarily take from the user
CARTESIA_API_URL = "https://api.cartesia.ai/v1/text-to-speech"
# Default voice ID (can be overridden if you add more options later)
DEFAULT_VOICE_ID = "c61e634d-5f60-4949-b3e6-c886016bdf5f" # Replace if needed with a valid one
DEFAULT_MODEL_ID = "sonic-english"
DEFAULT_OUTPUT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 24000

# --- Flask App Setup ---
app = Flask(__name__)

# --- Helper Function for Cartesia API Call ---
def call_cartesia_tts_stream(api_key: str, text: str):
    """
    Calls Cartesia API and returns the streaming response object or an error dict.
    """
    if not api_key or not text:
        return {"error": "API Key and Text are required.", "status_code": 400}

    headers = {
        "Cartesia-Version": "2024-05-10",  # Check for the latest version
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "voice_id": DEFAULT_VOICE_ID, # Using the default for simplicity
        "model_id": DEFAULT_MODEL_ID,
        "output_format": {
            "container": DEFAULT_OUTPUT_FORMAT,
            "encoding": "mp3", # Hardcoding based on container for now
            "sample_rate": DEFAULT_SAMPLE_RATE,
        },
    }

    try:
        response = requests.post(
            CARTESIA_API_URL, headers=headers, json=payload, stream=True
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response # Return the successful streaming response object

    except requests.exceptions.RequestException as e:
        error_message = f"Error connecting to Cartesia API: {e}"
        status_code = 500 # General server error for connection issues
        api_error_details = None

        # Try to get more specific error from Cartesia response if available
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            try:
                api_error_details = e.response.json()
                error_message = f"Cartesia API Error ({status_code}): {api_error_details.get('message', e.response.text)}"
            except ValueError: # Handle cases where response is not JSON
                error_message = f"Cartesia API Error ({status_code}): {e.response.text}"

        print(f"API Call Failed: {error_message}") # Log error server-side
        return {"error": error_message, "status_code": status_code, "details": api_error_details}

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": "An unexpected server error occurred.", "status_code": 500}


# --- Flask Routes ---
@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/generate_speech', methods=['POST'])
def generate_speech():
    """Handles the API call and streams audio back."""
    data = request.get_json()
    api_key = data.get('apiKey')
    text = data.get('text')

    # Call the helper function
    cartesia_response = call_cartesia_tts_stream(api_key, text)

    # Check if the helper returned an error dictionary
    if isinstance(cartesia_response, dict) and 'error' in cartesia_response:
        return jsonify({"error": cartesia_response.get("error", "Unknown error")}), cartesia_response.get("status_code", 500)

    # If no error, cartesia_response is the streaming requests.Response object
    # We need to stream this back to the client.
    # Use stream_with_context to efficiently stream the response.
    def generate_audio_chunks():
        try:
            for chunk in cartesia_response.iter_content(chunk_size=4096):
                yield chunk
        finally:
            cartesia_response.close() # Ensure the connection is closed

    # Return the streaming response to the browser
    return Response(
        stream_with_context(generate_audio_chunks()),
        mimetype=f'audio/{DEFAULT_OUTPUT_FORMAT}', # e.g., audio/mpeg for mp3
        headers={
            "Content-Disposition": "inline; filename=speech.mp3" # Suggest inline playback
            # Cartesia might include other relevant headers like Transfer-Encoding
            # which requests/Flask usually handle, but check if specific ones are needed.
        }
    )

# --- Run the App ---
if __name__ == '__main__':
    # Use port 5001 to avoid potential conflicts with default port 5000
    app.run(debug=True, port=5001) # debug=True for development (auto-reloads)