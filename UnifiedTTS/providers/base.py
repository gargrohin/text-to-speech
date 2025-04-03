# unified_tts/providers/base.py

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..exceptions import ConfigurationError

class BaseTTSProvider(ABC):
    """Abstract base class for all TTS providers."""

    def __init__(self, api_key: Optional[str] = None, api_key_env_var: Optional[str] = None, **kwargs):
        """
        Initializes the provider.

        Args:
            api_key: The API key (optional).
            api_key_env_var: The name of the environment variable for the API key (optional).
            **kwargs: Additional provider-specific configuration.
        """
        self.api_key = api_key or os.environ.get(api_key_env_var) if api_key_env_var else None
        if not self.api_key and api_key_env_var:
             # Only raise if the env var was specified but key not found directly or in env
             print(f"Warning: API key for {self.__class__.__name__} not found via argument or environment variable '{api_key_env_var}'. Provider might not work.")
             # Optional: Raise ConfigurationError immediately if key is absolutely required
             # raise ConfigurationError(f"API key for {self.__class__.__name__} is missing. Set the '{api_key_env_var}' environment variable or pass 'api_key'.")


        self._validate_config()
        self._initialize_client(**kwargs)

    def _validate_config(self):
        """Provider-specific validation of configuration (e.g., check for required keys)."""
        # Default implementation does nothing, override in subclasses if needed.
        pass

    def _initialize_client(self, **kwargs):
        """Provider-specific client initialization."""
        # Default implementation does nothing, override in subclasses.
        pass

    @abstractmethod
    def synthesize(self, text: str, output_format: str = 'mp3', **kwargs) -> bytes:
        """
        Synthesizes speech from text.

        Args:
            text: The text to synthesize.
            output_format: The desired audio output format (e.g., 'mp3', 'wav', 'opus').
                           Provider support may vary.
            **kwargs: Provider-specific options (e.g., voice, model, speed).

        Returns:
            bytes: The synthesized audio data.

        Raises:
            SynthesisError: If synthesis fails.
            ConfigurationError: If the provider is not properly configured.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the unique name identifier for the provider (e.g., 'openai')."""
        pass