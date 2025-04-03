# unified_tts/core.py

import os
from typing import Dict, Type, Optional, Any
from .exceptions import ProviderNotFoundError, SynthesisError
from .providers.base import BaseTTSProvider
from .providers.openai import OpenAITTSProvider
from .providers.cartesia import CartesiaTTSProvider # Placeholder

# Registry of available providers
# Add new providers here
AVAILABLE_PROVIDERS: Dict[str, Type[BaseTTSProvider]] = {
    OpenAITTSProvider.PROVIDER_NAME: OpenAITTSProvider,
    CartesiaTTSProvider.PROVIDER_NAME: CartesiaTTSProvider,
}

class UnifiedTTS:
    """
    A unified interface for interacting with multiple Text-to-Speech providers.
    """

    def __init__(self, config: Optional[Dict[str, Dict[str, Any]]] = None, **kwargs):
        """
        Initializes the UnifiedTTS instance and configures providers.

        Configuration can be provided in several ways (priority order):
        1. Direct provider kwargs: `UnifiedTTS(openai_api_key='sk-...', cartesia_voice_id='...')`
        2. `config` dictionary: `UnifiedTTS(config={'openai': {'api_key': 'sk-...'}, 'cartesia': {'voice_id': '...'}})`
        3. Environment variables (checked by individual providers if keys not passed).

        Args:
            config (Optional[Dict[str, Dict[str, Any]]]): A dictionary where keys
                are provider names (e.g., 'openai') and values are dictionaries
                of configuration options for that provider (e.g., {'api_key': '...', 'model': '...'}).
            **kwargs: Direct configuration options for providers, prefixed with the
                provider name and an underscore (e.g., `openai_api_key='...'`,
                `cartesia_api_key='...'`, `openai_model='tts-1-hd'`).
        """
        self.providers: Dict[str, BaseTTSProvider] = {}
        self._config = config or {}
        self._direct_kwargs = kwargs

        self._initialize_providers()

    def _initialize_providers(self):
        """Initializes provider instances based on configuration."""
        # Consolidate configuration
        effective_config = {}

        # Start with base config dictionary
        for provider_name, provider_config in self._config.items():
            if provider_name in AVAILABLE_PROVIDERS:
                effective_config.setdefault(provider_name, {}).update(provider_config)

        # Override or add with direct kwargs
        for key, value in self._direct_kwargs.items():
            parts = key.split('_', 1)
            if len(parts) == 2 and parts[0] in AVAILABLE_PROVIDERS:
                provider_name, config_key = parts
                effective_config.setdefault(provider_name, {})[config_key] = value
            # else: warn about unrecognized kwarg?

        # Instantiate configured providers
        for provider_name, provider_class in AVAILABLE_PROVIDERS.items():
            # Get specific config for this provider, or empty dict if none
            provider_conf = effective_config.get(provider_name, {})

            # Try to instantiate. Provider's __init__ handles env vars if keys missing here.
            # We wrap in try-except to allow selective provider initialization
            # based on available keys/config, without halting everything.
            try:
                # Pass the consolidated config dict to the provider's init
                instance = provider_class(**provider_conf)
                self.providers[provider_name] = instance
                print(f"INFO: Successfully initialized provider: {provider_name}")
            except Exception as e:
                 # Catch potential ConfigurationErrors or others during init
                 print(f"WARNING: Failed to initialize provider '{provider_name}': {e}. This provider will be unavailable.")


    def list_available_providers(self) -> list[str]:
        """Returns a list of successfully initialized provider names."""
        return list(self.providers.keys())

    def synthesize(
        self,
        text: str,
        provider: str,
        output_path: Optional[str] = None,
        output_format: Optional[str] = None, # Allow overriding default per call
        **kwargs
    ) -> Optional[bytes]:
        """
        Synthesizes speech using the specified provider.

        Args:
            text (str): The text to synthesize.
            provider (str): The name of the provider to use (e.g., 'openai', 'cartesia').
            output_path (Optional[str]): If provided, the audio will be saved to this
                                         file path instead of being returned as bytes.
            output_format (Optional[str]): The desired audio output format (provider-specific,
                                           e.g., 'mp3', 'wav'). Overrides provider default if set.
            **kwargs: Additional provider-specific parameters (e.g., voice, model, speed).
                      These are passed directly to the selected provider's synthesize method.

        Returns:
            Optional[bytes]: The synthesized audio data as bytes if `output_path` is None.
                             Returns None if `output_path` is provided and saving is successful.

        Raises:
            ProviderNotFoundError: If the requested provider is not available or initialized.
            SynthesisError: If the synthesis process fails within the provider.
            IOError: If saving the file fails when `output_path` is provided.
        """
        if provider not in self.providers:
            available = self.list_available_providers()
            raise ProviderNotFoundError(
                f"Provider '{provider}' not found or not initialized. "
                f"Available providers: {available}"
            )

        tts_provider = self.providers[provider]

        # Prepare synthesis arguments, allowing per-call output_format override
        synth_args = {}
        if output_format:
            synth_args['output_format'] = output_format
        synth_args.update(kwargs) # Add other specific params

        try:
            audio_bytes = tts_provider.synthesize(text, **synth_args)
        except SynthesisError:
            # Re-raise SynthesisError to propagate it
            raise
        except Exception as e:
            # Catch unexpected errors from provider implementation
            raise SynthesisError(f"Unexpected error during synthesis with provider '{provider}': {e}")


        if output_path:
            try:
                # Ensure directory exists if path includes directories
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                print(f"INFO: Audio successfully saved to: {output_path}")
                return None # Indicate success when saving to file
            except IOError as e:
                raise IOError(f"Failed to save audio to '{output_path}': {e}")
            except Exception as e:
                raise IOError(f"An unexpected error occurred while saving audio to '{output_path}': {e}")

        else:
            return audio_bytes