# unified_tts/__init__.py
from .core import UnifiedTTS
from .exceptions import UnifiedTTSError, ConfigurationError, ProviderNotFoundError, SynthesisError

__version__ = "0.1.0" # Example version

# Optional: make providers accessible if needed, though usually accessed via UnifiedTTS
# from .providers.openai import OpenAITTSProvider
# from .providers.cartesia import CartesiaTTSProvider