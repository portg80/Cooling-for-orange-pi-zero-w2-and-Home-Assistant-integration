from core.NLU.Word_to_Number_Russian.extractor import NumberExtractor

def test_number_conversion():
    extractor = NumberExtractor()

    # Test cases
    test_cases = [
        "установи громкость сорок",
        "поставь уровень на тридцать пять",
        "громкость десять",
        "увеличь на восемьдесят два",
        "снизь до пятнадцати",
        "выключи звук ноль",
        "просто текст без чисел"
    ]

    print("Testing number conversion:")
    for test in test_cases:
        result, _ = extractor.replace(test, apply_regrouping=True)
        print(f"'{test}' -> '{result}'")

if __name__ == "__main__":
    test_number_conversion()
