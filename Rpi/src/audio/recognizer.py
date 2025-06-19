import time
import base64
import logging
import requests
from typing import Optional
from settings import SPEECH_API_TOKEN, SPEECH_API_URL
from .model import Language
from .recorder import get_recorder

logger = logging.getLogger("recognizer")

def recognize(wav_path: str, language: Language) -> Optional[str]:
        with open(wav_path, 'rb') as f:
            audio_base64 = base64.b64encode(f.read()).decode()
        payload = {
            'lang': language.api_lang,
            'token': SPEECH_API_TOKEN,
            'audio': audio_base64
        }

        detect_text = "<{silent}>"
        for _ in range(3):
            try:
                response = requests.post(SPEECH_API_URL, data=payload, timeout=10)
                if response.status_code == 200:
                    detect_text = response.json().get('sentence', "<{silent}>")
                    logging.debug(f"detect_text: {detect_text}")
                    return detect_text
            except requests.RequestException:
                time.sleep(1)
        logging.debug(f"detect_text: {detect_text}")
        return detect_text

def recognize_direct(language: Language) -> int:
    """return direct_code:int"""
    while True:
        wav_file = get_recorder().record_speech()
        if not wav_file:
            continue

        result = recognize(wav_file, language).lower().strip('.!? ')
        if result != "<{silent}>":
            direct_code = language.direct_mapping.get(result)
            if direct_code is not None:
                return direct_code
            raise ValueError("辨識結果不在指定範圍內")
