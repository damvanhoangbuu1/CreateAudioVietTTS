import requests
from bs4 import BeautifulSoup
import asyncio
import nest_asyncio
import os
from common.text import *
from common.audio import *
from leech.wikisach import *

from argparse import ArgumentParser

nest_asyncio.apply()

semaphore = asyncio.Semaphore(10)

async def async_process_sentences(sentence):
    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, process_sentence, sentence)

async def process_audio_chapter(text, path):
    text = text.replace("\n", " ")
    arrText = split_text_into_sentences(text)
    tasks = []
    for i in range(len(arrText)):
        tasks.append(async_process_sentences({
            "text": arrText[i],
            "path": f"{path}/{i}",
            "track": i,
            "title": "",
            "album": "",
        }))
    await asyncio.gather(*tasks)

async def create_audio_chapter(chapter, dirAudio):
    failCnt = 0
    text = ''
    chapter_folder_path = dirAudio + f"/{str(chapter['track'])}"
    chapter_path = dirAudio + f"/{str(chapter['track'])}.mp3"
    while failCnt < 5 and text == '':
        response = requests.get(chapter['link'])
        soup = BeautifulSoup(response.content, "html.parser")
        text = get_chapter_content(soup).replace('"', '')
        text = text.replace('\n', ' ')
        text = text.replace('“', ' ')
        text = text.replace('”', ' ')
        text = text.replace('【 ', ' ')
        if text != '':
            print('-------------------------------------------------------')
            print('CREATING CHAPTER ', chapter['title'])
            if not os.path.exists(chapter_folder_path):
                # If the directory doesn't exist, create it.
                os.makedirs(chapter_folder_path)
            await process_audio_chapter(text, chapter_folder_path)
            merge_all_mp3_in_folder(chapter_folder_path, chapter_path)
            chapter['path'] = dirAudio + f"/{str(chapter['track'])}"
            addMetaData(chapter)
            print('CREATED CHAPTER ', chapter['title'])
        else:
            failCnt += 1
    return

async def process_chapter(chapter):
    current_path = os.getcwd()
    dirAudio = os.path.join(current_path + "/audio", remove_diacritics(chapter['album']))

    if not os.path.exists(dirAudio):
        # If the directory doesn't exist, create it.
        os.makedirs(dirAudio)

    await create_audio_chapter(chapter, dirAudio)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--link", default="https://wikisach.net/truyen/che-troi-khai-cuc-ta-co-the-cu-hien-ao-t-ZU4DzlS4CD8LOQRC", type=str)
    parser.add_argument("--start", default=0, type=int)
    parser.add_argument("--length", default=1, type=int)
    parser.add_argument("--track", default=0, type=int)

    args = parser.parse_args()

    chapters = get_all_chapter(args.link, args.start, args.length)

    print("Start: ", datetime.now())
    for chapter in chapters:
        asyncio.run(process_chapter(chapter))