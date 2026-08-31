import os
import time
import hashlib
import uuid
import base64
import subprocess
import concurrent.futures
import re
import sys
from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import threading

if getattr(sys, 'frozen', False):
    os.environ['WDM_LOG_LEVEL'] = '0'

CONFIG_FILE = "bot_config_multi_account.json"
CURRENT_VERSION = "6.6"
VERSION_URL = "https://raw.githubusercontent.com/username/repo-anda/main/version.json"
SECRET_KEY = "M4N1S_TRIAL_S3CR3T_2026"

URL_LOGIN = "https://www.fotoyu.com/login"
URL_TARGET_FOTO = "https://www.fotoyu.com/upload"
URL_TARGET_VIDEO = "https://www.fotoyu.com/upload"
TOTAL_MAKSIMAL_RUN = 1000000
KECEPATAN_KETIK_HURUF = 0.1

pause_event = threading.Event()
pause_event.set()
is_paused = False
is_paused_kompres = False

stats = {
    "total": 0,
    "uploaded": 0,
    "failed": 0,
    "duplicate": 0
}

saved_accounts = {}
app_license_key = ""

def get_hwid():
    mac = str(uuid.getnode())
    return hashlib.md5(mac.encode()).hexdigest().upper()[:12]

def verify_license(key, hwid):
    if not key:
        return False, "Lisensi kosong."
    try:
        decoded = base64.b64decode(key.encode()).decode('utf-8')
        parts = decoded.split('|')
        if len(parts) != 3:
            return False, "Format lisensi tidak valid."
        key_hwid, exp_time, signature = parts
        if key_hwid != hwid:
            return False, "Lisensi ini bukan untuk komputer ini."
        if float(exp_time) < time.time():
            return False, "Lisensi Anda sudah kedaluwarsa!"
        expected_sig = hashlib.sha256(f"{key_hwid}|{exp_time}|{SECRET_KEY}".encode()).hexdigest()[:16]
        if signature != expected_sig:
            return False, "Lisensi dipalsukan atau rusak."
        return True, "Valid"
    except Exception:
        return False, "Kunci lisensi rusak."

# Fungsi pembantu untuk mencetak log ke UI dan Console secara bersamaan
def cetak_log(log_callback, pesan):
    print(pesan)
    if log_callback:
        log_callback(pesan + "\n")

def ambil_semua_media(folder_path, jenis_media, log_callback=None):
    if jenis_media == "Video":
        format_didukung = ('.mp4', '.mov')
    elif jenis_media == "Foto":
        format_didukung = ('.jpg', '.jpeg', '.png')
    else:
        format_didukung = ()

    if not os.path.exists(folder_path):
        return []

    file_valid = []
    for nama_file in os.listdir(folder_path):
        path_lengkap = os.path.join(folder_path, nama_file)
        if os.path.isfile(path_lengkap) and nama_file.lower().endswith(format_didukung):
            file_valid.append(path_lengkap)
    return file_valid

def inisialisasi_browser(email):
    options = Options()
    safe_email = re.sub(r'[^a-zA-Z0-9]', '_', email)
    lokasi_sesi = os.path.join(os.getcwd(), f"FotoyuSession_{safe_email}")
    options.add_argument(f"--user-data-dir={lokasi_sesi}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--enable-webgl")
    options.add_argument("--ignore-gpu-blocklist")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("detach", True)
    return webdriver.Chrome(options=options)

def login_fotoyu(driver, email, password, log_callback=None):
    wait = WebDriverWait(driver, 15)
    cetak_log(log_callback, f"🔍 Memeriksa status sesi login untuk akun: {email}...")
    driver.get(URL_TARGET_FOTO)
    time.sleep(6)
    url_sekarang = driver.current_url.lower()
    indikator_login = driver.find_elements(By.XPATH, "//input[@type='file']")

    if len(indikator_login) == 0 or "login" in url_sekarang or url_sekarang == "https://www.fotoyu.com/":
        cetak_log(log_callback, "🔑 Sesi kosong. Memulai proses login otomatis...")
        try:
            try:
                tombol_masuk_awal = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='button' and @label='Masuk']")))
                driver.execute_script("arguments[0].click();", tombol_masuk_awal)
                time.sleep(3)
            except Exception:
                pass

            email_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'nama pengguna') or contains(@placeholder, 'email') or @type='text' or @type='email']")))
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(1)

            tombol_lanjut = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='button' and @label='Lanjut'] | //*[contains(translate(text(), 'LANJUT', 'lanjut'), 'lanjut') or @label='Lanjut']")))
            driver.execute_script("arguments[0].click();", tombol_lanjut)
            time.sleep(2)

            pass_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password' or @name='password']")))
            pass_input.clear()
            pass_input.send_keys(password)
            time.sleep(1)

            try:
                tombol_submit = driver.find_elements(By.XPATH, "//div[@data-testid='button' and @label='Masuk']")
                if tombol_submit:
                    driver.execute_script("arguments[0].click();", tombol_submit[-1])
                else:
                    pass_input.send_keys(Keys.RETURN)
            except:
                pass_input.send_keys(Keys.RETURN)

            time.sleep(8)
            driver.get(URL_TARGET_FOTO)
            time.sleep(5)

            url_setelah_login = driver.current_url.lower()
            indikator_upload = driver.find_elements(By.XPATH, "//input[@type='file']")

            if "login" not in url_setelah_login and len(indikator_upload) > 0:
                cetak_log(log_callback, "✅ Login berhasil terverifikasi! Melanjutkan proses upload...")
                return True
            raise Exception(f"Timeout verifikasi: Terjebak di URL '{url_setelah_login}'.")
        except Exception as e:
            cetak_log(log_callback, f"❌ Gagal login atau Gagal Verifikasi! ({e})")
            return False
    else:
        cetak_log(log_callback, "✅ Sesi ditemukan! Melewati tahap login...")
        return True

def jalankan_bot(email, password, folder_media, harga, deskripsi, fototree, jenis_media, batch_size,
                 root, lbl_total, lbl_uploaded, lbl_failed, lbl_duplicate, btn_start, btn_pause, log_callback=None):
    global is_paused
    driver = None
    try:
        if not os.path.exists(folder_media):
            cetak_log(log_callback, f"❌ Error: Folder sumber tidak ditemukan!")
            return

        kumpulan_media = ambil_semua_media(folder_media, jenis_media, log_callback)[:TOTAL_MAKSIMAL_RUN]
        total_media = len(kumpulan_media)

        if total_media == 0:
            cetak_log(log_callback, f"✅ GAGAL: Tidak ditemukan {jenis_media} siap proses di folder sumber.")
            return

        stats["total"] = total_media
        stats["uploaded"] = 0
        stats["failed"] = 0
        stats["duplicate"] = 0
        root.after(0, lambda: lbl_total.configure(text=f"Total:\n{stats['total']}"))
        root.after(0, lambda: lbl_uploaded.configure(text=f"Berhasil:\n{stats['uploaded']}"))
        root.after(0, lambda: lbl_failed.configure(text=f"Gagal:\n{stats['failed']}"))
        root.after(0, lambda: lbl_duplicate.configure(text=f"Duplikat:\n{stats['duplicate']}"))

        chunks = [kumpulan_media[i:i + batch_size] for i in range(0, total_media, batch_size)]
        driver = inisialisasi_browser(email)
        wait = WebDriverWait(driver, 10)

        if not login_fotoyu(driver, email, password, log_callback):
            driver.quit()
            return

        for index_batch, batch in enumerate(chunks):
            while len(driver.window_handles) >= 10:
                if not is_paused:
                    cetak_log(log_callback, "\n⚠️ [SISTEM PROTEKSI MEMORI AKTIF]")
                    cetak_log(log_callback, "⏸ Terdapat 10 tab terbuka! Bot otomatis dijeda.")
                    is_paused = True
                    pause_event.clear()
                    root.after(0, lambda: btn_pause.configure(text="▶ RESUME", fg_color="#2ECC71", hover_color="#27AE60"))
                pause_event.wait()
                time.sleep(1)

            pause_event.wait()
            cetak_log(log_callback, f"\n==================================================")
            cetak_log(log_callback, f"📦 MEMPROSES GELOMBANG {index_batch + 1}/{len(chunks)} ({len(batch)} File)")
            cetak_log(log_callback, f"==================================================")

            if index_batch == 0:
                url_saat_ini = URL_TARGET_FOTO if jenis_media == "Foto" else URL_TARGET_VIDEO
                if "upload" not in driver.current_url.lower():
                    driver.get(url_saat_ini)
                    time.sleep(2)
            else:
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                url_saat_ini = URL_TARGET_FOTO if jenis_media == "Foto" else URL_TARGET_VIDEO
                driver.get(url_saat_ini)
                time.sleep(2)

            pause_event.wait()

            input_elemen = None
            try:
                if jenis_media == "Foto":
                    input_elemen = driver.find_element(By.XPATH, "//*[contains(@class, 'PhotoContainer') or contains(@class, 'photo')]//input[@type='file']")
                else:
                    input_elemen = driver.find_element(By.XPATH, "//*[contains(@class, 'VideoContainer') or contains(@class, 'video')]//input[@type='file']")
            except:
                semua_input_file = driver.find_elements(By.XPATH, "//input[@type='file']")
                if len(semua_input_file) >= 2:
                    input_elemen = semua_input_file[0] if jenis_media == "Foto" else semua_input_file[1]
                elif len(semua_input_file) == 1:
                    input_elemen = semua_input_file[0]

            if input_elemen:
                try:
                    driver.execute_script("arguments[0].style.display = 'block';", input_elemen)
                    input_elemen.send_keys("\n".join(batch))
                except Exception:
                    continue
            else:
                continue

            jumlah_file = len(batch)
            try:
                wait_form = WebDriverWait(driver, 600)
                wait_form.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
                mulai_render = time.time()
                form_sebelumnya = 0
                waktu_stabil = 0

                while time.time() - mulai_render < 600:
                    pause_event.wait()
                    form_sekarang = len(driver.find_elements(By.TAG_NAME, "textarea"))
                    if form_sekarang >= jumlah_file: break
                    if form_sekarang == form_sebelumnya:
                        waktu_stabil += 1
                        if waktu_stabil >= 5: break
                    else:
                        waktu_stabil = 0
                    form_sebelumnya = form_sekarang
                    time.sleep(1)
            except:
                pass

            form_tersedia = len(driver.find_elements(By.TAG_NAME, "textarea"))
            for i in range(form_tersedia):
                pause_event.wait()
                try:
                    textareas = driver.find_elements(By.TAG_NAME, "textarea")
                    hargas = driver.find_elements(By.XPATH, "//*[contains(text(), 'Harga Dasar')]/following::input[1]")
                    fototrees = driver.find_elements(By.XPATH, "//input[@name='tagName' or contains(@placeholder, 'Fototree') or contains(@placeholder, 'Location')]")

                    if i >= len(textareas) or i >= len(hargas) or i >= len(fototrees): continue

                    val_deskripsi = textareas[i].get_attribute("value") or ""
                    val_harga = hargas[i].get_attribute("value") or ""
                    val_fototree = fototrees[i].get_attribute("value") or ""

                    if val_deskripsi.strip() == deskripsi and val_harga.strip() == harga and val_fototree.strip() == fototree:
                        continue

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textareas[i])
                    textareas[i].send_keys(Keys.CONTROL, "a")
                    textareas[i].send_keys(Keys.BACKSPACE)
                    textareas[i].send_keys(deskripsi)

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", hargas[i])
                    hargas[i].click()
                    hargas[i].send_keys(Keys.CONTROL, "a")
                    hargas[i].send_keys(Keys.BACKSPACE)
                    hargas[i].send_keys(harga)

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fototrees[i])
                    time.sleep(0.1)
                    fototrees[i].click()
                    time.sleep(0.1)
                    fototrees[i].send_keys(Keys.CONTROL, "a")
                    fototrees[i].send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)

                    for huruf in fototree:
                        fototrees[i].send_keys(huruf)
                        time.sleep(KECEPATAN_KETIK_HURUF)

                    menu_dropdown_xpath = "//div[contains(@class, 'Menu') or contains(@class, 'menu-list')]"
                    wait.until(EC.presence_of_element_located((By.XPATH, menu_dropdown_xpath)))
                    time.sleep(1)

                    opsi_xpath = f"({menu_dropdown_xpath}//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{fototree.lower()}')])[1]"
                    opsi_target = wait.until(EC.element_to_be_clickable((By.XPATH, opsi_xpath)))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", opsi_target)
                    time.sleep(0.1)
                    opsi_target.click()
                except:
                    pass

            pause_event.wait()
            try:
                tombol_unggah_list = driver.find_elements(By.XPATH, "//div[@label='Unggah' or @data-testid='button' or contains(@class, 'Button__StyledButton')][contains(., 'Unggah')]")
                for btn in tombol_unggah_list:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    driver.execute_script("arguments[0].click();", btn)

                cetak_log(log_callback, f"📤 Perintah upload gelombang {index_batch + 1} dikirim.")
                stats["uploaded"] += jumlah_file
                root.after(0, lambda: lbl_uploaded.configure(text=f"Berhasil:\n{stats['uploaded']}"))
            except Exception:
                pass

        cetak_log(log_callback, "\n🎉 SELURUH GELOMBANG TELAH DIKIRIM KE PROSES UPLOAD!")

    except Exception as e:
        cetak_log(log_callback, f"\n⛔ BOT ERROR UTAMA: {str(e)}")
    finally:
        root.after(0, lambda: btn_start.configure(state="normal"))
        root.after(0, lambda: btn_pause.configure(state="disabled"))