import os
import random

import numpy as np
from moviepy import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    ImageClip,
    ColorClip,
    concatenate_audioclips,
)


from moviepy import AudioFileClip
from gtts import gTTS
from moviepy import vfx


from deep_translator import GoogleTranslator, TranslationNotFound
from moviepy.audio import fx

video_folder = "videos"


video_files = [
    os.path.join(video_folder, f)
    for f in os.listdir(video_folder)
    if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
]

if not video_files:
    print("В папке с видео не найдено ни одного видео файла.")
    exit(1)

audio_folder = "music_mp3"

audio_files = [
    os.path.join(audio_folder, f)
    for f in os.listdir(audio_folder)
    if f.lower().endswith((".mp3"))
]

random.shuffle(audio_files)
random.shuffle(video_files)


def load_words_from_file(filename):
    """Загружает слова из .txt файла и возвращает список"""
    with open(filename, "r", encoding="utf-8") as file:
        words = [line.split("-")[0].strip().lower() for line in file]
        return words


def load_used_words_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        words = [line.strip().lower() for line in file]
        return words


def write_to_end_of_file(filename, string_to_write):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(string_to_write + "\n")


words = load_words_from_file("russian_words.txt")
used_words = load_used_words_from_file("used_words.txt")

print("Слова", len(words), words)
print("использованные слова", len(used_words), used_words)
words = list(set(words) - set(used_words))


print("Итог", len(words), words)

if len(words) == 0:
    print("Все слова в файле russian_words.txt уже использовались ранее")
    exit(1)


random.shuffle(words)


words_number = 6

if len(words) < words_number * len(video_files):
    print(
        "Не хватит слов!",
        "Количество слов:",
        len(words),
        "Количество видео",
        len(video_files),
        f"Нужно еще {words_number*len(video_files) -len(words)}",
    )
    exit(1)


for m in range(len(video_files)):
    selected_video = video_files[m]
    selected_audio = AudioFileClip(audio_files[m % len(audio_files)])

    while selected_audio.duration < 40:
        selected_audio = concatenate_audioclips([selected_audio, selected_audio])

    audio_file_background = selected_audio.subclipped(0, 40).with_effects(
        [fx.MultiplyVolume(0.1)]
    )

    translations = []
    audio_word_files = []
    audio_translation_files = []
    russian_words = []

    i = 0

    while i < words_number:
        word = words[i + m * words_number]
        write_to_end_of_file("used_words.txt", word)
        try:
            translation = GoogleTranslator(source="ru", target="en").translate(word)
        except TranslationNotFound:
            i += 1
            continue

        russian_words.append(word)
        translations.append(translation)
        print(f"Слово: {word}  |  Перевод: {translation}")
        audio_word_files.append(f"audio_word{i}.mp3")
        audio_translation_files.append(f"audio_translation{i}.mp3")

        tts_word = gTTS(text=word, lang="ru")
        tts_word.save(audio_word_files[i])

        tts_translation = gTTS(text=translation, lang="en")
        tts_translation.save(audio_translation_files[i])
        i += 1

    # 4. Загружаем видео
    video_clip = VideoFileClip(selected_video).with_effects([vfx.MultiplySpeed(0.5)])

    video_clip = concatenate_videoclips([video_clip, video_clip])

    # 5. Создаём текстовые оверлеи.
    # Параметры для текста (настройте шрифт, размер, цвет по желанию)
    font_size = 70
    color = "white"
    stroke_color = "black"
    stroke_width = 2
    circle_size = 100

    # Текст для оригинального слова – показываем первые 3 секунды

    audio_clip_words = []
    audio_clip_translations = []
    txt_clip_words = []
    txt_clip_translations = []

    intro_text = (
        TextClip(
            text="Переводи на английский",
            font_size=40,
            color="white",
            font="font_rus.ttf",
        )
        .with_position("center")
        .with_duration(1)
        .with_start(0)
    )

    countdown_clips = []

    def make_circle_mask(radius):
        """Создаём маску с белым кругом на чёрном фоне."""
        diameter = radius * 2
        mask = np.zeros((diameter, diameter), dtype=np.uint8)  # Черный фон
        y, x = np.ogrid[:diameter, :diameter]
        center = radius  # Центр круга
        mask[(x - center) ** 2 + (y - center) ** 2 <= radius**2] = (
            255  # Рисуем белый круг
        )
        return mask

    k = 3

    for i in range(words_number):
        txt_clip_word = TextClip(
            text=russian_words[i], font_size=50, color="white", font="font_rus.ttf"
        ).with_position("center")

        bg_clip = (
            ColorClip(
                size=(txt_clip_word.w + 30, txt_clip_word.h + 30), color=(0, 0, 0)
            )
            .with_duration(1)
            .with_position("center")
        )
        final_clip_word = (
            CompositeVideoClip([bg_clip, txt_clip_word])
            .with_position("center")
            .with_duration(1)
            .with_start(k)
        )
        txt_clip_words.append(final_clip_word)

        audio_clip_words.append(AudioFileClip(audio_word_files[i]).with_start(k))

        for j, num in enumerate([3, 2, 1]):
            circle_size = 200  # Размер круга
            mask_clip = ImageClip(make_circle_mask(circle_size), is_mask=True)
            bg_circle = (
                ColorClip(size=(circle_size, circle_size), color=(0, 0, 0))
                .with_mask(mask_clip)
                .with_position("center")
                .with_duration(1)
                .with_start(k + j + 1)
            )
            countdown_clips.append(bg_circle)

            countdown_text = (
                TextClip(
                    text=str(num), font_size=100, color="white", font="font_rus.ttf"
                )
                .with_position("center")
                .with_duration(1)
                .with_start(k + j + 1)
            )
            countdown_clips.append(countdown_text)

        k += 4
        txt_clip_translation = TextClip(
            text=translations[i], font_size=50, color=(66, 245, 135), font="font.ttf"
        ).with_position("center")
        bg_clip = (
            ColorClip(
                size=(txt_clip_translation.w + 30, txt_clip_translation.h + 30),
                color=(0, 0, 0),
            )
            .with_duration(1)
            .with_position("center")
        )
        final_clip_translation = (
            CompositeVideoClip([bg_clip, txt_clip_translation])
            .with_position("center")
            .with_duration(1)
            .with_start(k)
        )
        txt_clip_translations.append(final_clip_translation)

        audio_clip_translations.append(
            AudioFileClip(audio_translation_files[i]).with_start(k)
        )
        k += 2

    all_audio_clips = [audio_file_background]
    all_audio_clips.extend(audio_clip_words)
    all_audio_clips.extend(audio_clip_translations)

    composite_audio = CompositeAudioClip(all_audio_clips)

    # 7. Создаём финальный композитный клип с видео и наложенными текстовыми клипами.
    all_word_clips = (
        [video_clip]
        + [intro_text]
        + countdown_clips
        + txt_clip_words
        + txt_clip_translations
    )

    final_clip = CompositeVideoClip(all_word_clips)
    final_clip = final_clip.with_audio(composite_audio)

    # 8. Сохраняем итоговое видео.
    output_file = f"output/video_{m+1}.mp4"
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")

    # Опционально: удаляем временные аудио файлы
    try:
        for i in range(len(audio_word_files)):
            os.remove(audio_word_files[i])
            os.remove(audio_translation_files[i])
    except Exception:
        print("Файлы", audio_word_files, audio_translation_files, "не найдены ")
