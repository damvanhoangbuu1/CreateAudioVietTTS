from pydub import AudioSegment
import eyed3
import soundfile as sf
import os

from vietTTS.hifigan.mel2wave import mel2wave
from vietTTS.nat.text2mel import text2mel
from common.text import *
from datetime import datetime

def process_sentence(sentence):
    tmpText = nat_normalize_text(sentence["text"])
    mel = text2mel(tmpText, "assets/infore/lexicon.txt", 0.2)
    wave = mel2wave(mel)
    print("Saving audio to: ", sentence["path"], " time: ", datetime.now())
    sf.write(str(sentence["path"]+".wav"), wave, samplerate=16000)
    toMp3(sentence)

def toMp3(sentence):
    #convert mp3
    audio = AudioSegment.from_wav(str(sentence["path"]+".wav"))
    audio.export(sentence["path"]+".mp3", format="mp3")
    #add track, title, album
    addMetaData(sentence)

    if os.path.exists(sentence["path"]+".wav"):
        # If it exists, delete the file
        os.remove(sentence["path"]+".wav")

def addMetaData(sentence):
    audiofile = eyed3.load(sentence["path"]+".mp3")
    if audiofile is not None:
        audiofile.initTag()
        audiofile.tag.track_num = sentence["track"]
        audiofile.tag.album = sentence["title"]
        audiofile.tag.title = sentence["album"]
        audiofile.tag.save()

def merge_all_mp3_in_folder(input_folder, output_file):
    audio_files = [f for f in os.listdir(input_folder) if f.endswith(".mp3")]

    # Kiểm tra nếu không có file MP3 nào trong thư mục
    if not audio_files:
        print("Không có file MP3 trong thư mục.")
        return
    
    sorted_audio_files = sorted(audio_files, key=lambda x: int(''.join(filter(str.isdigit, os.path.splitext(x)[0]))))

    # Đọc và gộp các file MP3
    combined_audio = AudioSegment.silent(duration=0)
    for file in sorted_audio_files:
        file_path = os.path.join(input_folder, file)
        sound = AudioSegment.from_mp3(file_path)
        combined_audio += sound

    # Xuất file âm thanh gộp ra file MP3
    combined_audio.export(output_file, format="mp3")

    # Xóa thư mục
    for file in audio_files:
        file_path = os.path.join(input_folder, file)
        os.remove(file_path)
    
    os.removedirs(input_folder)