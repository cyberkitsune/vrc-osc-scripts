import abc
import deepl
import googletrans

registered_translators = {}

class VRCSubsTranslator(metaclass=abc.ABCMeta):
    """An abstract class that represents a possible translator for VRCSubs. Subclass this abstract class to make one
    """
    @abc.abstractclassmethod
    def __init__(self, args):
        """Constructs a VRCSubs translator and initalizes it.

        Args:
            args (str): If the translator requires any string arguments, such as an api key, specify them here.
        """
        pass

    @abc.abstractclassmethod
    def translate(self, source_lang, target_lang, text) -> str:
        """Translate given text from a given langage into a different one.

        Args:
            source_lang (str): The language code of the source language (unaltered)
            target_lang (str): The langugage code of the destination language (unaltered)
            text (str): The untranslated text

        Returns:
            str: The translated text
        """
        pass

    @abc.abstractclassmethod
    def conv_langcode(self, langcode) -> str:
        """Convert a standard language code into one supported by this translator.

        Args:
            langcode (str): The standard language code

        Returns:
            str: The translator-specific language code
        """
        return langcode


class RegisterTranslator(object):
    """This is a decorator that must be attached to your subclass of VRCSubsTranslator for the config file to be aware that it exists.
    """
    def __init__(self, translator_name):
        """Creates a translator registration for a CLASS

        Args:
            translator_name (str): The name of your translator as it will be set in the Config.yml
        """
        self.translator_name = translator_name

    def __call__(self, translator_class):
        global registered_translators
        registered_translators[self.translator_name] = translator_class


@RegisterTranslator("Google")
class GoogleTranslator(VRCSubsTranslator):
    def __init__(self, args):
        self.translator = googletrans.Translator()

    def conv_langcode(self, langcode) -> str:
        langsplit = langcode.split('-')[0]
        if langsplit == "zh":
            if langcode == "zh-CN":
                return langcode
            return "zh-TW"
        if langsplit == "yue":
            return "zh-TW"

        return langsplit

    def translate(self, source_lang, target_lang, text):
        output = None
        try:
            output = self.translator.translate(text=text, src=self.conv_langcode(source_lang), dest=self.conv_langcode(target_lang))
        except Exception as e:
            raise Exception("Failed to translate text!", e)
        
        if output is not None:
            return output.text
        else:
            return None


@RegisterTranslator("DeepL")
class DeepLTranslator(VRCSubsTranslator):
    def __init__(self, api_key):
        self.dtranslator = None
        try:
            self.dtranslator = deepl.Translator(api_key)
        except deepl.exceptions.DeepLException as e:
            raise Exception("Failed to initalize DeepL!", e)

    def conv_langcode(self, langcode) -> str:
        if langcode.upper() in ["EN-US","EN-GB","PT-BR","PT-PT"]:
            return langcode.upper()
        else:
            return langcode.split('-')[0]

    def translate(self, source_lang, target_lang, text) -> str:
        output = None
        try:
            output = self.dtranslator.translate_text(text=text, source_lang=self.conv_langcode(source_lang)[:2].upper(), target_lang=self.conv_langcode(target_lang).upper())
        except Exception as e:
            raise Exception("Failed to translate text!", e)
        if output is not None:
            return output.text
        else:
            return None