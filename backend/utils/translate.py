from googletrans import Translator

translator = Translator()

def deep_translate(data, lang):
    try:
        if isinstance(data, str):
            return translator.translate(data, dest=lang).text

        elif isinstance(data, list):
            return [deep_translate(i, lang) for i in data]

        elif isinstance(data, dict):
            return {k: deep_translate(v, lang) for k, v in data.items()}

        return data

    except Exception as e:
        print("Translation Error:", e)
        return data