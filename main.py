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
# نطاق المدة الطبيعي المقبول قبل الضبط الدقيق للسرعة (يحافظ على جودة الصوت)
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
        pass  # حتى لو فشل تسجيل الخطأ لا نوقف التنفيذ


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

    # احتياطي ثابت (الفاتحة) لو فشلت كل المحاولات مع كل القراء
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
    إن فشلت محاولة (تنزيل ناقص/مدة غير منطقية) يتم تنظيف الملفات وإعادة المحاولة بسورة أخرى.
    """
    last_error = None

    for global_try in range(1, MAX_BATCH_RETRIES + 1):
        ayahs, surah_name, reciter_name, surah_num, reciter_info = get_precise_quran_data()

        downloaded = []
        temp_files = []
        total_raw = 0.0
        ok = True

        for idx, ayah in enumerate(ayahs):
            audio_urls = build_ayah_urls(ayah, surah_num, reciter_info)
            temp_audio_name = f"precise_ayah_{global_try}_{idx}.mp3"

            success = fetch_audio_file(audio_urls, temp_audio_name)
            if not success:
                log_error("تنزيل صوت آية", Exception(f"تعذر تنزيل الآية رقم {idx + 1} من كل الروابط"))
                ok = False
                break

            temp_files.append(temp_audio_name)

            try:
                raw_audio = AudioFileClip(temp_audio_name)
                dur = raw_audio.duration
                if not dur or dur <= 0.1:
                    raise ValueError("مدة صوتية غير صالحة")
            except Exception as e:
                log_error(f"قراءة ملف صوت الآية {idx + 1}", e)
                ok = False
                break

            downloaded.append((ayah, raw_audio, dur, temp_audio_name))
            total_raw += dur

        if ok and len(downloaded) == AYAHS_COUNT and DURATION_TOLERANCE_MIN <= total_raw <= DURATION_TOLERANCE_MAX:
            return downloaded, surah_name, reciter_name, surah_num, total_raw

        # تنظيف كل شيء من هذه المحاولة الفاشلة قبل إعادة المحاولة بسورة/قارئ آخر
        for _, clip, _, _ in downloaded:
            try:
                clip.close()
            except Exception:
                pass
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

        last_error = Exception(
            f"محاولة {global_try}/{MAX_BATCH_RETRIES}: عدد الآيات المُحمّلة = {len(downloaded)}, "
            f"المدة الطبيعية = {round(total_raw, 1)}ث (خارج النطاق أو تحميل ناقص)"
        )
        log_error("تجميع دفعة الآيات", last_error)

    raise RuntimeError(f"تعذر تجميع {AYAHS_COUNT} آيات صالحة بعد {MAX_BATCH_RETRIES} محاولات. آخر سبب: {last_error}")


# =========================================================
#                     إرسال الفيديو لتيليجرام
# =========================================================

def send_video_to_telegram(filepath, caption_text, retries=3):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log_error("إرسال تيليجرام", Exception("لم يتم ضبط TELEGRAM_TOKEN أو TELEGRAM_CHAT_ID في متغيرات البيئة"))
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"

    for attempt in range(1, retries + 1):
        try:
            with open(filepath, 'rb') as video_file:
                response = requests.post(
                    url,
                    data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text},
                    files={'video': video_file},
                    timeout=90
                )
            if response.status_code == 200:
                return True
            log_error(
                f"إرسال تيليجرام - محاولة {attempt}/{retries}",
                Exception(f"رمز استجابة: {response.status_code} - {response.text[:200]}")
            )
        except Exception as e:
            log_error(f"إرسال تيليجرام - محاولة {attempt}/{retries}", e)
        time.sleep(3 * attempt)

    return False


# =========================================================
#                      الدالة الرئيسية للإنتاج
# =========================================================

def generate_video():
    font_path = None
    video_clips_pool = []
    raw_audio_clips = []
    temp_files_to_delete = []
    fps = 10

    try:
        font_path = retry(download_arabic_font, context="تحميل الخط", retries=3, delay=2)

        downloaded, surah_name, reciter_name, surah_num, total_raw = build_ayah_batch()
        temp_files_to_delete.extend([f for _, _, _, f in downloaded])
        raw_audio_clips.extend([clip for _, clip, _, _ in downloaded])

        # حساب عامل ضبط السرعة لجعل مجموع مدة الآيات الخمس = 30 ثانية بالضبط
        speed_factor = total_raw / TARGET_DURATION
        speed_factor = max(SPEED_FACTOR_MIN, min(SPEED_FACTOR_MAX, speed_factor))

        print(f"جاري معالجة {AYAHS_COUNT} آيات من {surah_name} بصوت {reciter_name} "
              f"(المدة الطبيعية: {round(total_raw, 1)}ث، عامل الضبط: {round(speed_factor, 3)})")

        total_duration = 0.0

        for idx, (ayah, raw_audio, raw_dur, _) in enumerate(downloaded):
            text = ayah['text']
            if idx == 0 and text.startswith("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ") and len(text) > 40:
                text = text.replace("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "").strip()

            try:
                audio_clip = raw_audio.fx(speedx, speed_factor).audio_fadein(0.05).audio_fadeout(0.05)
                duration = audio_clip.duration
            except Exception as e:
                log_error(f"ضبط سرعة صوت الآية {idx + 1}", e)
                audio_clip = raw_audio.audio_fadein(0.05).audio_fadeout(0.05)
                duration = raw_audio.duration

            text_chunks = split_long_text(text, max_words=5)
            num_chunks = len(text_chunks)
            chunk_duration = duration / num_chunks

            sub_clips = []
            for i, chunk in enumerate(text_chunks):
                start_audio = i * chunk_duration
                end_audio = min((i + 1) * chunk_duration, duration)
                actual_chunk_duration = max(end_audio - start_audio, 1.0 / fps)

                num_frames = max(1, int(actual_chunk_duration * fps))

                try:
                    frame = create_text_image(chunk, font_path)
                except Exception as e:
                    log_error(f"إنشاء صورة نصية للآية {idx + 1}", e)
                    frame = np.zeros((1920, 1080, 3), dtype=np.uint8)

                frames = [frame for _ in range(num_frames)]

                chunk_clip = ImageSequenceClip(frames, fps=fps)
                chunk_clip = chunk_clip.set_duration(actual_chunk_duration)

                chunk_audio = audio_clip.subclip(start_audio, end_audio)
                chunk_clip = chunk_clip.set_audio(chunk_audio)
                sub_clips.append(chunk_clip)

            ayah_final_clip = concatenate_videoclips(sub_clips, method="compose")
            video_clips_pool.append(ayah_final_clip)
            total_duration += duration

        if not video_clips_pool:
            raise ValueError("لم يتم إنتاج أي مقطع فيديو رغم نجاح تنزيل الصوت")

        print(f"مدة الفيديو الإجمالية بعد الضبط: {round(total_duration, 2)} ثانية لعدد {len(video_clips_pool)} آيات.")

        final_video_clip = concatenate_videoclips(video_clips_pool, method="compose")
        output_filename = "quran_chroma.mp4"

        retry(
            final_video_clip.write_videofile,
            output_filename,
            fps=fps, codec="libx264", audio_codec="aac",
            audio_fps=44100, audio_bitrate="192k", logger=None,
            context="ترميز الفيديو النهائي", retries=2, delay=3
        )

        final_video_clip.close()
        temp_files_to_delete.append(output_filename)

        caption_text = (
            f"📖 {surah_name} ({AYAHS_COUNT} آيات - 30 ثانية)\n"
            f"🎙️ تلاوة بترتيل {reciter_name}\n"
            f"✨ كروما سوداء عالية الدقة (1080x1920)\n\n"
            f"بواسطة المطور: {YOUR_NAME}"
        )

        sent = send_video_to_telegram(output_filename, caption_text)
        if sent:
            print("====================================")
            print(f"✅ تم إنشاء وإرسال فيديو {surah_name} بنجاح، المدة: {round(total_duration, 1)} ثانية "
                  f"({AYAHS_COUNT} آيات).")
            print("====================================")
        else:
            err = Exception("فشل إرسال الفيديو لتيليجرام بعد كل المحاولات (الفيديو تم إنشاؤه بنجاح محلياً)")
            log_error("إرسال تيليجرام", err)
            notify_telegram_error("إرسال الفيديو", err)

    except Exception as e:
        log_error("التنفيذ العام لـ generate_video", e)
        notify_telegram_error("التنفيذ العام", e)

    finally:
        for clip in video_clips_pool:
            try:
                clip.close()
            except Exception:
                pass
        for clip in raw_audio_clips:
            try:
                clip.close()
            except Exception:
                pass
        if font_path:
            # لا نحذف الخط فعلياً حتى لا نعيد تنزيله في كل تشغيل - إن رغبت بحذفه فعّل السطر التالي
            # temp_files_to_delete.append(font_path)
            pass
        for file in set(temp_files_to_delete):
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                log_error(f"حذف ملف مؤقت {file}", e)

        gc.collect()


# =========================================================
#                        نقطة التشغيل الرئيسية
# =========================================================

if __name__ == "__main__":
    for attempt in range(1, MAX_TOP_LEVEL_RETRIES + 1):
        try:
            generate_video()
            break
        except Exception as e:
            # طبقة حماية إضافية لأي خطأ غير متوقع خارج نطاق try الداخلي
            log_error(f"تشغيل كامل - محاولة {attempt}/{MAX_TOP_LEVEL_RETRIES}", e)
            if attempt == MAX_TOP_LEVEL_RETRIES:
                notify_telegram_error("فشل نهائي بعد كل المحاولات", e)
            else:
                time.sleep(5)
