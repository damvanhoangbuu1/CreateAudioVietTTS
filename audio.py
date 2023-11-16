import requests
from bs4 import BeautifulSoup
import re
import os
# from pathlib import Path
import soundfile as sf
import unicodedata
from common.text import *
from datetime import datetime

from vietTTS.hifigan.mel2wave import mel2wave
from vietTTS.nat.config import FLAGS
from vietTTS.nat.text2mel import text2mel

import asyncio
import nest_asyncio
from pydub import AudioSegment
import eyed3

nest_asyncio.apply()

semaphore = asyncio.Semaphore(10)

async def async_process_sentences(sentence):
    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, process_sentence, sentence)
    
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
    audiofile = eyed3.load(sentence["path"]+".mp3")
    if audiofile is not None:
        audiofile.initTag()
        audiofile.tag.track_num = sentence["track"]
        audiofile.tag.album = sentence["title"]
        audiofile.tag.title = sentence["album"]
        audiofile.tag.save()

    if os.path.exists(sentence["path"]+".wav"):
        # If it exists, delete the file
        os.remove(sentence["path"]+".wav")

async def create_audio_chapter(text, path, track, title, album):
    text = text.replace("\n", " ")
    arrText = split_text_into_sentences(text)
    tasks = []
    for i in range(len(arrText)):
        if i > 1:
            continue
        tasks.append(async_process_sentences({
            "text": arrText[i],
            "path": f"{path}_{i}",
            "track": track,
            "title": title,
            "album": album,
        }))
    await asyncio.gather(*tasks)
            

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

def get_book_name(book_link):
    response = requests.get(book_link)
    soup = BeautifulSoup(response.content, "html.parser")
    title_tag = soup.find_all('span', itemprop='name')
    return title_tag[2].text

async def create_list_chapter_audio(bookName, dirAudio, chapter_link, Seq, success_count_max):
    success_count = 0

    while chapter_link and success_count < success_count_max:
        empty_content_count = 0
        while empty_content_count < 5:
            response = requests.get(chapter_link)
            soup = BeautifulSoup(response.content, "html.parser")

            title_tag = soup.find('h1')
            chapter_title = title_tag.find('a').text

            content_tag = soup.find(id="content")

            if content_tag:
                for tag in content_tag.find_all(['a', 'div']):
                    if tag.name == 'a' or tag.name == 'div':
                        if 'c-c' not in tag.get('class', []):
                            tag.extract()

            full_text = "\n\n\n".join(content_tag.stripped_strings)

            chapter_content = full_text

            if not chapter_content:
                empty_content_count += 1
                if empty_content_count == 5:

                    return
            else:
                path=f"{dirAudio}/Chuong{Seq:04d}"
                await create_audio_chapter(chapter_content, path, Seq, chapter_title, bookName)

                print(chapter_link)
                Seq += 1
                success_count += 1

                if success_count >= success_count_max:
                    return

                next_chapter_tag = soup.find(id="nextchap")
                next_chapter_link = next_chapter_tag.get(
                    'href') if next_chapter_tag else None

                if not next_chapter_link:
                    return
                
                chapter_link = next_chapter_link
    return

async def process_book(line):
    book_link = line.split(',')[0]
    seq = int(line.split(',')[1])
    bookName = get_book_name(book_link)
    current_path = os.getcwd()
    dirAudio = os.path.join(current_path + "/audio", remove_diacritics(bookName))

    if not os.path.exists(dirAudio):
        # If the directory doesn't exist, create it.
        os.makedirs(dirAudio)

    await create_list_chapter_audio(bookName, dirAudio, book_link, seq, 1)

if __name__ == "__main__":
    print("Start: ", datetime.now())
    file = open("leech.txt", 'r')
    lines = file.readlines()
    for line in lines:
        asyncio.run(process_book(line.rstrip()))