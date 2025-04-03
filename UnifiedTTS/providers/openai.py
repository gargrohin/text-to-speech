# unified_tts/providers/openai.py

import os
from typing import Optional, Dict, Any
from ..exceptions import ConfigurationError, SynthesisError
from .base import BaseTTSProvider

# Try importing openai, handle if not installed
try:
    import openai
except ImportError:
    openai = None # Set to None if not installed

class OpenAITTSProvider(BaseTTSProvider):
    """TTS Provider implementation for OpenAI."""

    PROVIDER_NAME = "openai"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        if openai is None:
            raise ImportError("The 'openai' package is not installed. Please install it: pip install openai")
        super().__init__(api_key=api_key, api_key_env_var="OPENAI_API_KEY", **kwargs)
        self.client = None # Initialized in _initialize_client

    def _validate_config(self):
        """Ensure API key is present."""
        if not self.api_key:
            raise ConfigurationError(
                f"OpenAI API key is missing. Set the 'OPENAI_API_KEY' environment variable or pass 'api_key' during initialization."
            )

    def _initialize_client(self, **kwargs):
        """Initializes the OpenAI client."""
        try:
            self.client = openai.OpenAI(api_key=self.api_key, **kwargs) # Pass extra kwargs to client if needed
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize OpenAI client: {e}")

    @property
    def name(self) -> str:
        return self.PROVIDER_NAME

    def synthesize(self, text: str, output_format: str = 'mp3', **kwargs) -> bytes:
        """
        Synthesizes speech using OpenAI TTS.

        Args:
            text: The text to synthesize.
            output_format: Desired audio format (e.g., 'mp3', 'opus', 'aac', 'flac').
            **kwargs:
                voice (str): The voice to use (e.g., 'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'). Defaults to 'alloy'.
                model (str): The model to use (e.g., 'tts-1', 'tts-1-hd'). Defaults to 'tts-1'.
                speed (float): Speed multiplier (0.25 to 4.0). Defaults to 1.0.
                response_format (str): Overrides output_format if provided directly.

        Returns:
            bytes: The synthesized audio data.

        Raises:
            SynthesisError: If the OpenAI API call fails.
            ConfigurationError: If the client is not initialized.
        """
        if not self.client:
             raise ConfigurationError("OpenAI client not initialized. Check configuration.")

        # Prepare parameters for OpenAI API
        params = {
            'input': text,
            'voice': kwargs.get('voice', 'alloy'),
            'model': kwargs.get('model', 'tts-1'),
            'response_format': kwargs.get('response_format', output_format),
            'speed': kwargs.get('speed', 1.0),
        }

        try:
            response = self.client.audio.speech.create(**params)
            # The response object has a .content attribute with the audio bytes
            audio_bytes = response.content
            return audio_bytes
        except openai.APIError as e:
            raise SynthesisError(f"OpenAI API error during synthesis: {e}")
        except Exception as e:
            # Catch other potential errors (network issues, etc.)
            raise SynthesisError(f"An unexpected error occurred during OpenAI synthesis: {e}")