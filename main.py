import os
import random
import requests
import numpy as np
import gc
import time
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageSequenceClip, concatenate_videoclips

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

# إضافة معرفات everyayah كخطة احتياطية للسيرفر الأول
RECITERS = [
    {"name": "الشيخ محمد صديق المنشاوي", "id": "ar.minshawi", "everyayah_folder": "Minshawy_Murattal_128kbps"},
    {"name": "الشيخ ياسر الدوسري", "id": "ar.yasseraddussary", "everyayah_folder": "Yasser_Ad-Dussary_128kbps"},
    {"name": "الشيخ محمود خليل الحصري", "id": "ar.husary", "everyayah_folder": "Husary_128kbps"},
    {"name": "الشيخ السيد سعيد", "id": "ar.sayyidsaeed", "everyayah_folder": "Sayeed_Sayeed_64kbps"},
    {"name": "الشيخ حسن صالح", "id": "ar.hasansalih", "everyayah_folder": "Hasan_Salih_128kbps"}
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
        for attempt in range(3):
            try:
                r = requests.get(font_url, timeout=20)
                with open(font_path, "wb") as f:
                    f.write(r.content)
                break
            except Exception as e:
                print(f"⚠️ محاولة {attempt + 1} لتنزيل الخط فشلت: {e}")
                time.sleep(2)
    return font_path

def create_text_image(text, font_path, width=1080, height=1920):
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 65)
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
            r = requests.get(api_url, timeout=20)
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
                return selected_ayahs, surah_name, reciter['name'], surah_num, reciter
        except Exception as e:
            print(f"⚠️ خطأ أثناء جلب السورة من الـ API (محاولة {attempts}): {e}")
            time.sleep(1)
            
    fallback_ayahs = [
        {"text": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ", "number": 262, "numberInSurah": 255}
    ]
    return fallback_ayahs, "سورة البقرة", "الشيخ محمود خليل الحصري", 2, RECITERS[2]

# دالة مخصصة لتحميل الصوت مع معالجة الأخطاء ورابط احتياطي
def fetch_audio_file(audio_urls, temp_audio_name):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in audio_urls:
        if not url:
            continue
            
        for attempt in range(3): # المحاولة 3 مرات لكل رابط
            try:
                r = requests.get(url, timeout=25, headers=headers, verify=False)
                if r.status_code == 200:
                    with open(temp_audio_name, "wb") as f:
                        f.write(r.content)
                    return True
            except requests.exceptions.RequestException as e:
                print(f"⚠️ فشل اتصال عند التنزيل من {url} (محاولة {attempt + 1}/3): {e}")
                time.sleep(2 * (attempt + 1))
                
    return False

def generate_video():
    ayahs, surah_name, reciter_name, surah_num, reciter_info = get_precise_quran_data()
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
            
            ayah_global_num = ayah.get('number')
            ayah_in_surah = ayah.get('numberInSurah')
            
            # بناء قائمة الروابط الأساسية والبديلة (Primary + Fallback CDN)
            audio_urls = []
            if ayah.get('audio'):
                audio_urls.append(ayah.get('audio'))
            
            if ayah_global_num:
                audio_urls.append(f"https://cdn.islamic.network/quran/audio/128/{reciter_info['id']}/{ayah_global_num}.mp3")
                
            if ayah_in_surah and 'everyayah_folder' in reciter_info:
                # سيرفر احتياطي من everyayah
                s_str = str(surah_num).zfill(3)
                a_str = str(ayah_in_surah).zfill(3)
                audio_urls.append(f"https://www.everyayah.com/data/{reciter_info['everyayah_folder']}/{s_str}{a_str}.mp3")
                
            temp_audio_name = f"precise_ayah_{idx}.mp3"
            
            # محاولة تحميل الملف بأمان مع تفادي الأخطاء
            success = fetch_audio_file(audio_urls, temp_audio_name)
            if not success:
                print(f"❌ التجاوز عن الآية رقم {idx+1} لعدم التمكن من جلب الصوت.")
                continue
                
            temp_files_to_delete.append(temp_audio_name)
            
            try:
                raw_audio = AudioFileClip(temp_audio_name)
                audio_clip = raw_audio.audio_fadein(0.05).audio_fadeout(0.05)
                duration = audio_clip.duration
            except Exception as e:
                print(f"⚠️ ملف الصوت تالف أو متعذر قراءته: {e}")
                continue
            
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
            raise ValueError("لم يتم إنتاج أي مقطع بسبب مشاكل بالاتصال.")
            
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
        
        # إرسال إلى تيليجرام مع إعادة المحاولة
        for attempt in range(3):
            try:
                with open(output_filename, 'rb') as video_file:
                    response = requests.post(
                        url,
                        data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text},
                        files={'video': video_file},
                        timeout=60
                    )
                if response.status_code == 200:
                    print("====================================")
                    print(f"تم إنشاء فيديو {surah_name} بمقاس ممتاز ومدة {round(total_duration)} ثانية! ✅")
                    print("====================================")
                    break
                else:
                    print(f"⚠️ فشل إرسال الملف لتيليجرام (رمز: {response.status_code})")
            except Exception as e:
                print(f"⚠️ فشل إرسال الفيديو لتيليجرام، محاولة {attempt+1}: {e}")
                time.sleep(3)
            
        temp_files_to_delete.append(output_filename)
            
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
            except Exception:
                pass
        
        gc.collect()

if __name__ == "__main__":
    generate_video()
