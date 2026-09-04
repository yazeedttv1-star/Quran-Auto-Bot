import os
import random
import requests
import numpy as np
import gc
import time
import traceback
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# محاولة استيراد moviepy بطريقة متوافقة مع الإصدارات المختلفة
try:
    # محاولة الاستيراد من الإصدارات الحديثة (2.x)
    from moviepy import (
        AudioFileClip, 
        ImageClip, 
        concatenate_videoclips,
        afx
    )
except ImportError:
    try:
        # محاولة الاستيراد من الإصدارات القديمة (1.x)
        from moviepy.editor import (
            AudioFileClip, 
            ImageClip, 
            concatenate_videoclips,
            afx
        )
    except ImportError:
        # محاولة الاستيراد من المسار القديم الآخر
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.video.VideoClip import ImageClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips
        import moviepy.audio.fx.all as afx

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Telegram configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YOUR_NAME = "yazeed"

# Quran reciters data
RECITERS = [
    {"name": "الشيخ محمد صديق المنشاوي", "id": "ar.minshawi", "everyayah_folder": "Minshawy_Murattal_128kbps"},
    {"name": "الشيخ ياسر الدوسري", "id": "ar.yasseraddussary", "everyayah_folder": "Yasser_Ad-Dussary_128kbps"},
    {"name": "الشيخ محمود خليل الحصري", "id": "ar.husary", "everyayah_folder": "Husary_128kbps"},
    {"name": "الشيخ السيد سعيد", "id": "ar.sayyidsaeed", "everyayah_folder": "Sayeed_Sayeed_64kbps"},
    {"name": "الشيخ حسن صالح", "id": "ar.hasansalih", "everyayah_folder": "Hasan_Salih_128kbps"},
]

# Constants
HISTORY_FILE = "history.txt"
ERROR_LOG_FILE = "error_log.txt"
AYAHS_COUNT = 5
TARGET_DURATION = 30.0
DURATION_TOLERANCE_MIN = 15.0
DURATION_TOLERANCE_MAX = 50.0
SPEED_FACTOR_MIN = 0.8
SPEED_FACTOR_MAX = 1.35
MAX_BATCH_RETRIES = 6
MAX_TOP_LEVEL_RETRIES = 2

def log_error(context, exc):
    """Log errors to file and console"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{ts}] ❌ خطأ في ({context}): {exc}\n{traceback.format_exc()}\n{'-' * 60}\n"
    print(f"⚠️ [{context}] {exc}")
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg)
    except Exception:
        pass

def notify_telegram_error(context, exc):
    """Send error notification via Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        text = f"⚠️ فشل بوت آيات القرآن في التنفيذ.\nالمرحلة: {context}\nالتفاصيل: {str(exc)[:300]}"
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': text}, timeout=20)
    except Exception as e:
        log_error("إرسال تنبيه خطأ لتيليجرام", e)

def get_viewed_history():
    """Get viewed verses history"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            log_error("قراءة ملف السجل", e)
    return set()

def save_to_history(entry):
    """Save verse to history"""
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception as e:
        log_error("حفظ السجل", e)

def download_arabic_font():
    """Download Arabic font if not exists"""
    font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
    font_path = "Amiri-Regular.ttf"
    if os.path.exists(font_path):
        return font_path
    try:
        r = requests.get(font_url, timeout=20)
        r.raise_for_status()
        with open(font_path, "wb") as f:
            f.write(r.content)
        return font_path
    except Exception as e:
        log_error("تحميل الخط العربي", e)
        return None

def create_text_image(text, font_path, width=1080, height=1920):
    """Create image with Arabic text centered"""
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        if font_path and os.path.exists(font_path):
            # Try with different font sizes
            font_size = 50
            font = ImageFont.truetype(font_path, font_size)
            
            # Check if text fits, if not reduce font size
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Reduce font size if text is too wide
            if text_width > width - 100:
                font_size = int(font_size * (width - 100) / text_width)
                font = ImageFont.truetype(font_path, max(20, font_size))
        else:
            font = ImageFont.load_default()
    except Exception as e:
        log_error("تحميل الخط لإنشاء صورة النص", e)
        font = ImageFont.load_default()
    
    # Get final text dimensions
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Center text
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill=(255, 255, 255), font=font)
    
    return np.array(img)

def get_precise_quran_data():
    """Fetch Quran verses with reciter data"""
    history = get_viewed_history()
    reciters_order = RECITERS[:]
    random.shuffle(reciters_order)
    
    for reciter in reciters_order:
        for attempts in range(15):
            surah_num = random.randint(1, 114)
            api_url = f"https://api.alquran.cloud/v1/surah/{surah_num}/{reciter['id']}"
            try:
                r = requests.get(api_url, timeout=20)
                if r.status_code != 200:
                    continue
                data = r.json()['data']
                surah_name = data['name']
                ayahs = data['ayahs']
                total_ayahs = len(ayahs)
                
                if total_ayahs < AYAHS_COUNT:
                    continue
                
                start_idx = random.randint(0, total_ayahs - AYAHS_COUNT)
                selected_ayahs = ayahs[start_idx:start_idx + AYAHS_COUNT]
                
                history_entry = f"{surah_num}_{start_idx}_{reciter['id']}"
                if history_entry in history:
                    continue
                
                save_to_history(history_entry)
                return selected_ayahs, surah_name, reciter['name'], surah_num, reciter
            except Exception as e:
                log_error(f"جلب سورة {surah_num}", e)
                time.sleep(1)
    
    # Fallback to Surah Al-Fatihah
    fallback_ayahs = [
        {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "number": 1, "numberInSurah": 1},
        {"text": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "number": 2, "numberInSurah": 2},
        {"text": "الرَّحْمَٰنِ الرَّحِيمِ", "number": 3, "numberInSurah": 3},
        {"text": "مَالِكِ يَوْمِ الدِّينِ", "number": 4, "numberInSurah": 4},
        {"text": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", "number": 5, "numberInSurah": 5},
    ]
    return fallback_ayahs, "سورة الفاتحة", "الشيخ محمود خليل الحصري", 1, RECITERS[2]

def fetch_audio_file(audio_urls, temp_audio_name):
    """Download audio file from URLs"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in audio_urls:
        if not url:
            continue
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=25, headers=headers, verify=False)
                if r.status_code == 200 and len(r.content) > 1024:
                    with open(temp_audio_name, "wb") as f:
                        f.write(r.content)
                    return True
            except requests.exceptions.RequestException as e:
                log_error(f"تنزيل صوت من {url}", e)
                time.sleep(2)
    return False

def build_ayah_urls(ayah, surah_num, reciter_info):
    """Build audio URLs for an ayah"""
    audio_urls = []
    if ayah.get('audio'):
        audio_urls.append(ayah.get('audio'))
    
    ayah_global_num = ayah.get('number')
    ayah_in_surah = ayah.get('numberInSurah')
    
    if ayah_global_num:
        audio_urls.append(f"https://cdn.islamic.network/quran/audio/128/{reciter_info['id']}/{ayah_global_num}.mp3")
    
    if ayah_in_surah and 'everyayah_folder' in reciter_info:
        s_str = str(surah_num).zfill(3)
        a_str = str(ayah_in_surah).zfill(3)
        audio_urls.append(f"https://www.everyayah.com/data/{reciter_info['everyayah_folder']}/{s_str}{a_str}.mp3")
    
    return audio_urls

def build_ayah_batch():
    """Build batch of verses with audio"""
    for global_try in range(1, MAX_BATCH_RETRIES + 1):
        ayahs, surah_name, reciter_name, surah_num, reciter_info = get_precise_quran_data()
        downloaded = []
        total_raw = 0.0
        batch_success = True
        
        for i, ayah in enumerate(ayahs):
            temp_audio_name = f"temp_ayah_{i}.mp3"
            urls = build_ayah_urls(ayah, surah_num, reciter_info)
            
            success = fetch_audio_file(urls, temp_audio_name)
            if not success:
                batch_success = False
                break
            
            try:
                clip = AudioFileClip(temp_audio_name)
                if clip.duration is None:
                    batch_success = False
                    clip.close()
                    break
                total_raw += clip.duration
                downloaded.append((ayah, temp_audio_name, clip))
            except Exception as e:
                log_error(f"تحميل المقطع {temp_audio_name}", e)
                batch_success = False
                break
        
        if batch_success and (DURATION_TOLERANCE_MIN <= total_raw <= DURATION_TOLERANCE_MAX):
            return downloaded, surah_name, reciter_name, total_raw
        
        # Cleanup failed batch
        for _, temp_name, clip in downloaded:
            try:
                clip.close()
                if os.path.exists(temp_name):
                    os.remove(temp_name)
            except Exception as e:
                log_error("تنظيف الملفات المؤقتة", e)
        
        gc.collect()
    
    raise RuntimeError("تعذر تجميع دفعة آيات صالحة ضمن حدود المحاولات المسموحة.")

def generate_video():
    """Generate video with Quran verses and recitation"""
    font_path = download_arabic_font()
    downloaded, surah_name, reciter_name, total_raw = build_ayah_batch()
    
    audio_clips = []
    video_data = []
    
    # Calculate speed factor
    speed_factor = total_raw / TARGET_DURATION
    speed_factor = max(SPEED_FACTOR_MIN, min(SPEED_FACTOR_MAX, speed_factor))
    
    try:
        for ayah, audio_file, a_clip in downloaded:
            # Apply speed change
            adjusted_audio = afx.speedx(a_clip, factor=speed_factor)
            audio_clips.append(adjusted_audio)
            
            # Create text image
            display_text = f"{ayah['text']}\n\n[{surah_name} - {reciter_name}]"
            img_frame = create_text_image(display_text, font_path)
            
            # Create video clip from image
            duration = adjusted_audio.duration
            if duration is None or duration <= 0:
                duration = 3.0  # Fallback duration
            
            # Store video data for later processing
            video_data.append((img_frame, duration))
        
        # Concatenate audio
        final_audio = concatenate_videoclips(audio_clips)
        
        # Create video clips list using moviepy's ImageClip
        video_clips = []
        for i, (img_frame, duration) in enumerate(video_data):
            # Create ImageClip from numpy array
            clip = ImageClip(img_frame)
            clip = clip.with_duration(duration)
            video_clips.append(clip)
        
        # Concatenate video clips
        final_video = concatenate_videoclips(video_clips, method="compose")
        final_video = final_video.with_audio(final_audio)
        
        # Write video file
        output_filename = "quran_video.mp4"
        final_video.write_videofile(
            output_filename,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None  # Disable progress bar for cleaner output
        )
        
        # Close clips to free memory
        final_video.close()
        final_audio.close()
        for clip in video_clips:
            clip.close()
        
        return output_filename
    
    finally:
        # Cleanup temporary files
        for _, audio_file, a_clip in downloaded:
            try:
                a_clip.close()
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception as e:
                log_error("تنظيف الملفات المؤقتة", e)
        
        # Close all audio clips
        for clip in audio_clips:
            try:
                clip.close()
            except:
                pass
        
        gc.collect()

if __name__ == "__main__":
    for attempt in range(1, MAX_TOP_LEVEL_RETRIES + 1):
        try:
            print(f"🔄 بدء محاولة {attempt}...")
            video_path = generate_video()
            if video_path and os.path.exists(video_path):
                print(f"✅ تم إنشاء الفيديو بنجاح: {video_path}")
                print(f"📁 حجم الفيديو: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
                break
            else:
                raise RuntimeError("لم يتم إنشاء الفيديو بشكل صحيح")
        except Exception as err:
            log_error(f"التشغيل الرئيسي (محاولة {attempt})", err)
            if attempt == MAX_TOP_LEVEL_RETRIES:
                notify_telegram_error("التشغيل الرئيسي", err)
                raise err
            time.sleep(3)  # Wait before retry
