import unicodedata
import re
from vietTTS.nat.config import FLAGS

def split_text_into_sentences(text):
    sentences = []
    current_sentence = []

    sentence_endings = ("...", "..", ".", "!!!","!!","?")

    for char in text:
        current_sentence.append(char)

        if char in sentence_endings and len(current_sentence) > 1000:
            sentence = "".join(current_sentence).strip()
            sentences.append(sentence)
            current_sentence = []

    if current_sentence:
        sentence = "".join(current_sentence).strip()
        sentences.append(sentence)

    return sentences

def contains_lowercase_letters(text):
    pattern = re.compile(r'[a-z]')
    return bool(pattern.search(text))

def remove_diacritics(text):
    normalized_string = unicodedata.normalize('NFD', text)
    result = []
    capitalize_next_char = True

    for char in normalized_string:
        if unicodedata.category(char) != 'Mn':
            if char.isalpha():
                if capitalize_next_char:
                    result.append(char.upper())
                    capitalize_next_char = False
                else:
                    result.append(char.lower())
            else:
                result.append(char)
                capitalize_next_char = True

    result_string = ''.join(result)
    return re.sub(r'[\W_]', '', result_string)

def nat_normalize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.lower().strip()
    sil = FLAGS.special_phonemes[FLAGS.sil_index]
    text = re.sub(r"[\n.,:]+", f" {sil} ", text)
    text = text.replace('"', " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[.,:;?!]+", f" {sil} ", text)
    text = re.sub("[ ]+", " ", text)
    text = re.sub(f"( {sil}+)+ ", f" {sil} ", text)
    return text.strip()

def number_to_text_vietnamese(number):
    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    teens = ["", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi", "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"]
    hundreds = ["", "một trăm", "hai trăm", "ba trăm", "bốn trăm", "năm trăm", "sáu trăm", "bảy trăm", "tám trăm", "chín trăm"]
    thousands = ["", "một nghìn", "hai nghìn", "ba nghìn", "bốn nghìn", "năm nghìn", "sáu nghìn", "bảy nghìn", "tâm nghìn", "chín nghìn"]

    if number == 0:
        return "không"

    result = ""

    #xử lí hàng nghìn
    if number >= 1000:
        result += thousands[number // 1000] + " "
        number %= 1000
        if number < 100:
            result += "không trăm "


    # Xử lý hàng trăm
    if number >= 100:
        result += hundreds[number // 100] + " "
        number %= 100
        if number < 10:
            result += "linh "

    # Xử lý hàng chục:
    if number >= 10:
        result += teens[number // 10] + " "
        number %= 10

    # Xử lý đơn vị
    if number == 1 and "linh" not in result and "mười" not in result:
        result += "mốt"
    else:
        result += units[number]

    return result

def replace_numbers_with_text_vietnamese(text):
    for i in range(9999, 0, -1):
        text = text.replace(str(i), number_to_text_vietnamese(i))

    return text