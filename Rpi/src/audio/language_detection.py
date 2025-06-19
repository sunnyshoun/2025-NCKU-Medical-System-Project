import time
from .model import Language
from .recognizer import recognize
from .recorder import get_recorder
from settings import LANG_JP, LANG_EN, LANG_ZH, LANG_TW

LANGUAGE_MODELS = {
    "ja": Language(LANG_JP, "Japanese", {"うえ": 1, "上": 1, "した": 3, "下": 3, "左": 2, "右": 0, "みぎ": 0}),
    "en": Language(LANG_EN, "English", {"up": 1, "down": 3, "left": 2, "right": 0}),
    "zh-TW": Language(LANG_ZH, "STT for course", {"上": 1, "上面": 1, "下": 3, "下面": 3, "左": 2, "左邊": 2, "右": 0, "右邊": 0, "yo": 0}),
    "ta": Language(LANG_TW, "TA Phoneme", {
        "t-ing* p-ing*": 1, "t-ing* k-uan*": 1, "e* b-in*": 3, "e* kh-a*": 3,
        "t-o* p-ing*": 2, "t-o* tsh-iu* p-ing*": 2, "ts-iann* tsh-iu* p-ing*": 0, "ts-iann* p-ing*": 0
    })
}


def detect_language(timeout_seconds: float = 30.0) -> Language:
    language_keywords = {
        "中文": "zh-TW", "國語": "zh-TW",
        "English": "en", "英語": "en",
        "日本語": "ja", "t-ai* g-i*": "ta"
    }

    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        wav_file = get_recorder().record_speech(max_duration=5.0)
        if not wav_file:
            continue

        for lang in LANGUAGE_MODELS.values():
            result = recognize(wav_file, lang)
            if result and result != "<{silent}>":
                for keyword, detected_code in language_keywords.items():
                    if keyword in result:
                        return LANGUAGE_MODELS[detected_code]

    raise TimeoutError("語言偵測逾時")
