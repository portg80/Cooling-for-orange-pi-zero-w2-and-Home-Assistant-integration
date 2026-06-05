from core.NLU.Word_to_Number_Russian.extractor import NumberExtractor

class NumberConverter:
    def __init__(self):
        self.extractor = NumberExtractor()

    def convert_words_to_numbers(self, text):
        """
        Convert Russian number words to numerals in the given text.
        For example: "установи громкость сорок" -> "установи громкость 40"
        Returns tuple: (converted_text, was_converted)
        """
        try:
            converted_text, _ = self.extractor.replace(text, apply_regrouping=True)
            # Check if conversion actually happened by comparing with original text
            was_converted = converted_text != text
            return converted_text, was_converted
        except Exception as e:
            # If conversion fails, return original text
            print(f"Warning: Number conversion failed for text '{text}': {e}")
            return text, False
