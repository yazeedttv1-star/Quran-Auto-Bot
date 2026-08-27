import os
import random
import requests
import numpy as np
import gc
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageSequenceClip, concatenate_videoclips

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

RECITERS = [
    {"name": "الشيخ محمد صديق المنشاوي", "id": "ar.minshawi"},
    {"name": "الشيخ ياسر الدوسري", "id": "ar.yasseraddussary"},
    {"name": "الشيخ محمود خليل الحصري", "id": "ar.husary"},
    {"name": "الشيخ السيد سعيد", "id": "ar.sayyidsaeed"},
    {"name": "الشيخ حسن صالح", "id": "ar.hasansalih"}
]

HISTORY_FILE = "history.txt"

def get_viewed_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception:
            pass
    return set()

def save_to_history(entry):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception as e:
        print(f"⚠️ تحذير: لم يتم حفظ السجل: {e}")

def download_arabic_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            r = requests.get(font_url, timeout=15)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"⚠️ فشل جلب الخط المخصص: {e}")
    return font_path

# تكبير الأبعاد لتكون 1080x1920 (Full HD Vertical) لمنع ظهور النصوص بشكل صغير
def create_text_image(text, font_path, width=1080, height=1920):
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 65) # خط أكبر ومناسب
    except Exception:
        font = ImageFont.load_default()
        
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill=(255, 255, 255), font=font)
    return np.array(img)

def split_long_text(text, max_words=5):
    words = text.split()
    if len(words) <= max_words:
        return [text]
    
    chunks = []
    current_chunk = []
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_words:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def get_precise_quran_data():
    reciter = random.choice(RECITERS)
    history = get_viewed_history()
    
    attempts = 0
    while attempts < 15:
        attempts += 1
        surah_num = random.randint(1, 100)
        
        api_url = f"https://api.alquran.cloud/v1/surah/{surah_num}/{reciter['id']}"
        try:
            r = requests.get(api_url, timeout=15)
            if r.status_code == 200:
                data = r.json()['data']
                surah_name = data['name']
                ayahs = data['ayahs']
                total_ayahs = len(ayahs)
                
                if total_ayahs < 12:
                    continue
                
                start_idx = random.randint(0, max(0, total_ayahs - 10))
                selected_ayahs = ayahs[start_idx:]
                
                history_entry = f"{surah_num}_{start_idx}_{reciter['id']}"
                if history_entry in history:
                    continue
                    
                save_to_history(history_entry)
                return selected_ayahs, surah_name, reciter['name'], surah_num, reciter['id']
        except Exception as e:
            print(f"⚠️ خطأ أثناء جلب السورة: {e}")
            
    fallback_ayahs = [
        {"text": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ", "number": 262}
    ]
    return fallback_ayahs, "سورة البقرة", "الشيخ محمود خليل الحصري", 2, "ar.husary"

def generate_video():
    ayahs, surah_name, reciter_name, surah_num, reciter_id = get_precise_quran_data()
    font_path = download_arabic_font()
    
    video_clips_pool = []
    temp_files_to_delete = []
    total_duration = 0.0
    TARGET_DURATION = 30.0
    
    print(f"جاري معالجة مقطع ~30 ثانية لـ {surah_name} بصوت {reciter_name}...")
    
    fps = 10
    
    try:
        for idx, ayah in enumerate(ayahs):
            if total_duration >= TARGET_DURATION:
                break
                
            text = ayah['text']
            if idx == 0 and text.startswith("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ") and len(text) > 40:
                text = text.replace("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "").strip()
            
            # الحصول على رابط الصوت بأمان دون حدوث KeyError
            audio_url = ayah.get('audio')
            if not audio_url:
                ayah_number = ayah.get('number')
                audio_url = f"https://cdn.islamic.network/quran/audio/128/{reciter_id}/{ayah_number}.mp3"
                
            temp_audio_name = f"precise_ayah_{idx}.mp3"
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(audio_url, timeout=15, headers=headers, verify=False)
            if r.status_code != 200:
                continue
                
            with open(temp_audio_name, "wb") as f:
                f.write(r.content)
            temp_files_to_delete.append(temp_audio_name)
            
            raw_audio = AudioFileClip(temp_audio_name)
            audio_clip = raw_audio.audio_fadein(0.05).audio_fadeout(0.05)
            duration = audio_clip.duration
            
            if duration <= 0.1:
                duration = 2.0
                
            if total_duration + duration > TARGET_DURATION + 3:
                allowed_duration = TARGET_DURATION - total_duration
                if allowed_duration > 3.0:
                    audio_clip = audio_clip.subclip(0, allowed_duration)
                    duration = allowed_duration
                else:
                    break
            
            text_chunks = split_long_text(text, max_words=5)
            num_chunks = len(text_chunks)
            chunk_duration = duration / num_chunks
            
            sub_clips = []
            for i, chunk in enumerate(text_chunks):
                start_audio = i * chunk_duration
                end_audio = min((i + 1) * chunk_duration, duration)
                actual_chunk_duration = end_audio - start_audio
                
                num_frames = int(actual_chunk_duration * fps)
                if num_frames == 0:
                    num_frames = 1
                    
                frames = [create_text_image(chunk, font_path) for _ in range(num_frames)]
                
                chunk_clip = ImageSequenceClip(frames, fps=fps)
                chunk_clip = chunk_clip.set_duration(actual_chunk_duration)
                
                chunk_audio = audio_clip.subclip(start_audio, end_audio)
                chunk_clip = chunk_clip.set_audio(chunk_audio)
                sub_clips.append(chunk_clip)
                
            ayah_final_clip = concatenate_videoclips(sub_clips, method="compose")
            video_clips_pool.append(ayah_final_clip)
            total_duration += duration
            
        if not video_clips_pool:
            raise ValueError("لم يتم إنشاء مقاطع.")
            
        print(f"مدة الفيديو الإجمالية: {round(total_duration, 1)} ثانية.")
        final_video_clip = concatenate_videoclips(video_clips_pool, method="compose")
        
        output_filename = "quran_chroma.mp4"
        final_video_clip.write_videofile(
            output_filename,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            audio_fps=44100,
            audio_bitrate="192k",
            logger=None
        )
        
        final_video_clip.close()
        for clip in video_clips_pool:
            clip.close()
            
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
        caption_text = (
            f"📖 {surah_name} (مقطع 30 ثانية)\n"
            f"🎙️ تلاوة بترتيل {reciter_name}\n"
            f"✨ كروما سوداء عالية الدقة (1080x1920)\n\n"
            f"بواسطة المطور: {YOUR_NAME}"
        )
        
        with open(output_filename, 'rb') as video_file:
            response = requests.post(
                url,
                data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text},
                files={'video': video_file}
            )
            
        temp_files_to_delete.append(output_filename)
        
        if response.status_code == 200:
            print("====================================")
            print(f"تم إنشاء فيديو {surah_name} بمقاس ممتازي ومدة {round(total_duration)} ثانية! ✅")
            print("====================================")
        else:
            print(f"⚠️ فشل إرسال الملف لتيليجرام: {response.status_code}")
            
    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")
        
    finally:
        for clip in video_clips_pool:
            try:
                clip.close()
            except Exception:
                pass
        
        temp_files_to_delete.append(font_path)
        for file in temp_files_to_delete:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                pass
        
        gc.collect()

if __name__ == "__main__":
    generate_video()
