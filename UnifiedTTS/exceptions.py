# unified_tts/exceptions.py

class UnifiedTTSError(Exception):
    """Base exception for the unified_tts library."""
    pass

class ConfigurationError(UnifiedTTSError):
    """Error related to configuration (e.g., missing API keys)."""
    pass

class ProviderNotFoundError(UnifiedTTSError):
    """Error when a requested TTS provider is not found or configured."""
    pass

class SynthesisError(UnifiedTTSError):
    """Error during the speech synthesis process."""
    pass