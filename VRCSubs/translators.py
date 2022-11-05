import abc
import deepl
import googletrans

registered_translators = {}

class VRCSubsTranslator(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def __init__(self, args) -> None:
        pass

    @abc.abstractclassmethod
    def translate(self, source_lang, target_lang, text) -> str:
        pass

    @abc.abstractclassmethod
    def conv_langcode(self, langcode) -> str:
        return langcode


class RegisterTranslator(object):

    def __init__(self, translator_name):
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
            self.dtranslator.translate_text(text=text, source_lang=self.conv_langcode(source_lang)[:2].upper(), target_lang=self.conv_langcode(target_lang)[:2].upper())
        except Exception as e:
            raise Exception("Failed to translate text!", e)
        if output is not None:
            return output.text
        else:
            return None