"""Free Google Translate API for Python. Translates totally free of charge."""
__all__ = 'TextTranslator', 'WordTranslator'
__version__ = '3.1.0-alpha'


from googletrans.client import TextTranslator
from googletrans.clientN import WordTranslator
from googletrans.constants import LANGCODES, LANGUAGES  # noqa
from googletrans.constantsN import LANGCODES, LANGUAGES  # noqa
