import os
import random
import requests
import numpy as np
import gc
import time
import traceback
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageSequenceClip, concatenate_videoclips
from moviepy.audio.fx.all import speedx

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
    {"name": "الشيخ حسن صالح", "id": "ar.hasansalih", "everyayah_folder": "Hasan_Salih_128kbps"},
]

HISTORY_FILE = "history.txt"
ERROR_LOG_FILE = "error_log.txt"

AYAHS_COUNT = 5           # عدد الآيات الثابت لكل فيديو
TARGET_DURATION = 30.0    # المدة المستهدفة بالثواني
DURATION_TOLERANCE_MIN = 24.0
DURATION_TOLERANCE_MAX = 40.0
SPEED_FACTOR_MIN = 0.8
SPEED_FACTOR_MAX = 1.35

MAX_BATCH_RETRIES = 6        # عدد محاولات اختيار دفعة آيات صالحة
MAX_TOP_LEVEL_RETRIES = 2    # عدد محاولات تشغيل السكربت كاملاً


# =========================================================
#                    نظام تسجيل ومعالجة الأخطاء
# =========================================================

def log_error(context, exc):
    """يسجل الخطأ في ملف السجل مع الوقت والتفاصيل الكاملة، بدون إيقاف التنفيذ"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{ts}] ❌ خطأ في ({context}): {exc}\n{traceback.format_exc()}\n{'-' * 60}\n"
    print(f"⚠️ [{context}] {exc}")
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg)
    except Exception:
        pass


def notify_telegram_error(context, exc):
    """يرسل تنبيهاً نصياً بسيطاً لتيليجرام عند فشل التنفيذ نهائياً بعد كل المحاولات"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        text = f"⚠️ فشل بوت آيات القرآن في التنفيذ.\nالمرحلة: {context}\nالتفاصيل: {str(exc)[:300]}"
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': text}, timeout=20)
    except Exception as e:
        log_error("إرسال تنبيه خطأ لتيليجرام", e)


def retry(func, *args, context="عملية", retries=3, delay=2, default=None, **kwargs):
    """منفذ عام يعيد محاولة أي دالة تلقائياً عند حدوث خطأ، مع تأخير متصاعد"""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            log_error(f"{context} - محاولة {attempt}/{retries}", e)
            if attempt < retries:
                time.sleep(delay * attempt)
    if default is not None:
        return default
    raise last_exc


# =========================================================
#                          السجل التاريخي
# =========================================================

def get_viewed_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            log_error("قراءة ملف السجل", e)
    return set()


def save_to_history(entry):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception as e:
        log_error("حفظ السجل", e)


# =========================================================
#                       الخط والنصوص
# =========================================================

def download_arabic_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
    font_path = "Amiri-Regular.ttf"
    if os.path.exists(font_path):
        return font_path
    r = requests.get(font_url, timeout=20)
    r.raise_for_status()
    with open(font_path, "wb") as f:
        f.write(r.content)
    return font_path


def create_text_image(text, font_path, width=1080, height=1920):
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 65)
    except Exception as e:
        log_error("تحميل الخط لإنشاء صورة النص", e)
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


# =========================================================
#                    جلب بيانات القرآن (5 آيات متتالية)
# =========================================================

def get_precise_quran_data():
    """يختار سورة عشوائية ويعيد 5 آيات متتالية لم تُعرض من قبل"""
    history = get_viewed_history()
    reciters_order = RECITERS[:]
    random.shuffle(reciters_order)

    for reciter in reciters_order:
        attempts = 0
        while attempts < 15:
            attempts += 1
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
                log_error(f"جلب سورة {surah_num} بصوت {reciter['name']} (محاولة {attempts})", e)
                time.sleep(1)
                continue

    fallback_ayahs = [
        {"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "number": 1, "numberInSurah": 1},
        {"text": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "number": 2, "numberInSurah": 2},
        {"text": "الرَّحْمَٰنِ الرَّحِيمِ", "number": 3, "numberInSurah": 3},
        {"text": "مَالِكِ يَوْمِ الدِّينِ", "number": 4, "numberInSurah": 4},
        {"text": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", "number": 5, "numberInSurah": 5},
    ]
    return fallback_ayahs, "سورة الفاتحة", "الشيخ محمود خليل الحصري", 1, RECITERS[2]


# =========================================================
#                        تحميل الصوت
# =========================================================

def fetch_audio_file(audio_urls, temp_audio_name):
    """يحاول تنزيل الصوت من عدة روابط احتياطية بالترتيب"""
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
                log_error(f"تنزيل صوت من {url} (محاولة {attempt + 1}/3)", e)
                time.sleep(2 * (attempt + 1))

    return False


def build_ayah_urls(ayah, surah_num, reciter_info):
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


# =========================================================
#          تجميع دفعة من 5 آيات صالحة (مع تصحيح ذاتي)
# =========================================================

def build_ayah_batch():
    """
    يحاول عدة مرات جلب 5 آيات وتنزيل صوتها بنجاح، ضمن مدة زمنية طبيعية معقولة.
    """
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
                total_raw += clip.duration
                downloaded.append((ayah, temp_audio_name, clip))
            except Exception as e:
                log_error(f"خطأ في تحميل المقطع الصوتي {temp_audio_name}", e)
                batch_success = False
                break

        if batch_success and (DURATION_TOLERANCE_MIN <= total_raw <= DURATION_TOLERANCE_MAX):
            return downloaded, surah_name, reciter_name, total_raw

        # تنظيف الملفات المؤقتة عند إخفاق الدفعة
        for _, temp_name, clip in downloaded:
            try:
                clip.close()
                if os.path.exists(temp_name):
                    os.remove(temp_name)
            except Exception as e:
                log_error("تنظيف الملفات المؤقتة", e)

        gc.collect()

    raise RuntimeError("تعذر تجميع دفعة آيات صالحة ضمن حدود المحاولات المسموحة.")


# =========================================================
#                     إنشاء الفيديو
# =========================================================

def generate_video():
    font_path = download_arabic_font()
    downloaded, surah_name, reciter_name, total_raw = build_ayah_batch()

    audio_clips = []
    video_clips = []

    speed_factor = total_raw / TARGET_DURATION
    speed_factor = max(SPEED_FACTOR_MIN, min(SPEED_FACTOR_MAX, speed_factor))

    try:
        for ayah, audio_file, a_clip in downloaded:
            adjusted_audio = speedx(a_clip, factor=speed_factor)
            audio_clips.append(adjusted_audio)

            display_text = f"{ayah['text']}\n\n[{surah_name} - {reciter_name}]"
            img_frame = create_text_image(display_text, font_path)

            v_clip = ImageSequenceClip([img_frame], fps=1).set_duration(adjusted_audio.duration)
            video_clips.append(v_clip)

        final_audio = concatenate_videoclips(audio_clips).audio
        final_video = concatenate_videoclips(video_clips, method="compose")
        final_video.audio = final_audio

        output_filename = "quran_video.mp4"
        final_video.write_videofile(
            output_filename,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4
        )
        return output_filename

    finally:
        for _, audio_file, a_clip in downloaded:
            a_clip.close()
            if os.path.exists(audio_file):
                os.remove(audio_file)
        gc.collect()


if __name__ == "__main__":
    for attempt in range(1, MAX_TOP_LEVEL_RETRIES + 1):
        try:
            video_path = generate_video()
            print(f"تم إنشاء الفيديو بنجاح: {video_path}")
            break
        except Exception as err:
            log_error(f"فشل في التشغيل الرئيسي (محاولة {attempt})", err)
            if attempt == MAX_TOP_LEVEL_RETRIES:
                notify_telegram_error("التشغيل الرئيسي لإنشاء الفيديو", err)
