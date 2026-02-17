# processor.py
import re


class TextCleaner:
    @staticmethod
    def clean(text):
        if not text: return ""
        arabic_norm = re.compile(r'[^\u0600-\u06FF0-9\s\.\!\؟\،\؛]')
        text = arabic_norm.sub(' ', text)

        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def is_valuable(text):
        return len(text.split()) > 30