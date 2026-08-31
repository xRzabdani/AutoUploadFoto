import os
import sys
import json
import time
import threading
import subprocess
import urllib.request
import multiprocessing
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import deque

import customtkinter as ctk
from PIL import Image, ImageTk
import psutil

# --- Import Matplotlib untuk Grafik ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import seluruh variabel dan fungsi dari bot_core
import bot_core

# ======================================================================
# KELAS UNTUK MENGALIHKAN PRINT KE DALAM APLIKASI
# ======================================================================
class RedirectText:
    def __init__(self, text_ctrl, root):
        self.output = text_ctrl
        self.root = root

    def write(self, string):
        self.root.after(0, self._write, string)

    def _write(self, string):
        self.output.insert(tk.END, string)
        self.output.see(tk.END)

    def flush(self): pass

# ======================================================================
# FUNGSI AUTO-UPDATE OTOMATIS (FORCE UPDATE)
# ======================================================================
def cek_update_otomatis(root):
    try:
        req = urllib.request.urlopen(bot_core.VERSION_URL, timeout=5)
        data = json.loads(req.read().decode('utf-8'))
        remote_version = data.get("version")
        download_url = data.get("url")
        changelog = data.get("changelog", "Pembaruan sistem tersedia.")

        if remote_version and remote_version != bot_core.CURRENT_VERSION:
            root.after(0, lambda: _prompt_update(remote_version, changelog, download_url, root))
    except Exception:
        pass

def _prompt_update(remote_version, changelog, download_url, root):
    messagebox.showinfo(
        "Update Sistem Diperlukan 🚀",
        f"Sistem menemukan versi baru ({remote_version})!\n\nPerubahan:\n{changelog}\n\nSistem akan diperbarui otomatis sekarang. Harap tunggu sebentar..."
    )
    jalankan_proses_update(download_url, root)

def jalankan_proses_update(url_download, root):
    try:
        temp_dir = os.environ.get("TEMP", "C:\\Temp")
        file_baru_path = os.path.join(temp_dir, "update_baru.exe")

        urllib.request.urlretrieve(url_download, file_baru_path)
        app_path = os.path.abspath(sys.argv[0])

        bat_path = os.path.join(temp_dir, "updater.bat")
        with open(bat_path, "w") as f:
            f.write(f"""
            @echo off
            timeout /t 2 /nobreak > nul
            del /f /q "{app_path}"
            move /y "{file_baru_path}" "{app_path}"
            start "" "{app_path}"
            del "%~f0"
            """)

        subprocess.Popen(bat_path, shell=True)
        root.destroy()
        sys.exit()
    except Exception as e:
        messagebox.showerror("Error Update", f"Gagal mengunduh pembaruan otomatis: {e}")

# ======================================================================
# FUNGSI MANAJEMEN AKUN & CONFIG
# ======================================================================
def simpan_akun(entry_email, entry_password, combo_akun):
    email = entry_email.get().strip()
    password = entry_password.get().strip()
    if not email or not password:
        messagebox.showwarning("Peringatan", "Email dan Password tidak boleh kosong!")
        return
    bot_core.saved_accounts[email] = password
    perbarui_combobox_akun(combo_akun, entry_email, entry_password, email)
    save_config_data(None, None, combo_akun, None, None, None, None, None, None, None, None, None, None, None)
    messagebox.showinfo("Sukses", f"Akun {email} berhasil disimpan!")

def hapus_akun(entry_email, entry_password, combo_akun):
    email = combo_akun.get().strip()
    if email in bot_core.saved_accounts:
        del bot_core.saved_accounts[email]
        entry_email.delete(0, tk.END)
        entry_password.delete(0, tk.END)
        perbarui_combobox_akun(combo_akun, entry_email, entry_password)
        save_config_data(None, None, combo_akun, None, None, None, None, None, None, None, None, None, None, None)
        messagebox.showinfo("Sukses", f"Akun {email} berhasil dihapus dari daftar!")
    else:
        messagebox.showwarning("Peringatan", "Pilih akun yang valid untuk dihapus.")

def perbarui_combobox_akun(combo_akun, entry_email, entry_password, pilih_email=None):
    combo_akun.configure(values=list(bot_core.saved_accounts.keys()))
    if pilih_email and pilih_email in bot_core.saved_accounts:
        combo_akun.set(pilih_email)
    elif bot_core.saved_accounts:
        first_email = list(bot_core.saved_accounts.keys())[0]
        combo_akun.set(first_email)
        on_pilih_akun(first_email, combo_akun, entry_email, entry_password)
    else:
        combo_akun.set("")

def on_pilih_akun(choice, combo_akun, entry_email, entry_password):
    email = choice.strip()
    if email in bot_core.saved_accounts:
        entry_email.delete(0, tk.END)
        entry_email.insert(0, email)
        entry_password.delete(0, tk.END)
        entry_password.insert(0, bot_core.saved_accounts[email])

def save_config_data(entry_email=None, entry_password=None, combo_akun=None, combo_jenis=None, entry_batch=None,
                     entry_folder=None, entry_harga=None, entry_fototree=None, entry_deskripsi=None,
                     entry_komp_sumber=None, entry_komp_tujuan=None, combo_jenis_komp=None, entry_nama_app=None,
                     entry_logo_path=None):
    data = {
        "license_key": bot_core.app_license_key,
        "accounts": bot_core.saved_accounts,
        "last_account": combo_akun.get() if combo_akun else "",
        "jenis": combo_jenis.get() if combo_jenis else "Foto",
        "batch": entry_batch.get() if entry_batch else "50",
        "folder": entry_folder.get() if entry_folder else "",
        "harga": entry_harga.get() if entry_harga else "50000",
        "fototree": entry_fototree.get() if entry_fototree else "",
        "deskripsi": entry_deskripsi.get("1.0", tk.END).strip() if entry_deskripsi else "",
        "komp_sumber": entry_komp_sumber.get() if entry_komp_sumber else "",
        "komp_tujuan": entry_komp_tujuan.get() if entry_komp_tujuan else "",
        "komp_jenis": combo_jenis_komp.get() if combo_jenis_komp else "Foto",
        "app_name": entry_nama_app.get() if entry_nama_app else f"Upload Manis V{bot_core.CURRENT_VERSION}",
        "logo_path": entry_logo_path.get() if entry_logo_path else ""
    }
    try:
        with open(bot_core.CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

# ======================================================================
# INISIALISASI TAMPILAN UTAMA
# ======================================================================
def show_main_app(root, konfig_termuat=None):
    for widget in root.winfo_children():
        widget.destroy()

    threading.Thread(target=cek_update_otomatis, args=(root,), daemon=True).start()

    ctk.set_appearance_mode("dark")
    COLOR_BG = "#000000"           
    COLOR_SURFACE = "#0A0A0A"      
    COLOR_BORDER = "#27272A"       
    COLOR_PRIMARY = "#FFFFFF"      
    COLOR_MUTED = "#A1A1AA"        
    COLOR_DL = "#10B981" 
    COLOR_UL = "#3B82F6" 
    
    root.configure(fg_color=COLOR_BG)
    root.title(f"Upload Manis V{bot_core.CURRENT_VERSION}")

    font_logo = ctk.CTkFont(family="Segoe UI Variable Display", size=20, weight="bold")
    font_title = ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold")
    font_input = ctk.CTkFont(family="Segoe UI", size=13)
    font_btn = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
    font_number = ctk.CTkFont(family="Consolas", size=32, weight="bold")

    def cari_direktori(entry_widget):
        d = filedialog.askdirectory(title="Pilih Folder")
        if d:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, d)
            
    def cari_file_logo(entry_widget):
        f = filedialog.askopenfilename(title="Pilih Logo", filetypes=[("Image Files", "*.ico *.png *.jpg *.jpeg")])
        if f:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, f)

    # ================= LOGIKA BOT =================
    def toggle_pause(btn_pause):
        if bot_core.is_paused:
            bot_core.pause_event.set()
            btn_pause.configure(text="⏸ JEDA", fg_color="#F59E0B", hover_color="#D97706")
        else:
            bot_core.pause_event.clear()
            btn_pause.configure(text="▶ LANJUT", fg_color="#10B981", hover_color="#059669")
        bot_core.is_paused = not bot_core.is_paused

    def toggle_pause_kompres(btn_pause_komp):
        if bot_core.is_paused_kompres:
            bot_core.pause_event.set()
            btn_pause_komp.configure(text="⏸ JEDA", fg_color="#F59E0B", hover_color="#D97706")
        else:
            bot_core.pause_event.clear()
            btn_pause_komp.configure(text="▶ LANJUT", fg_color="#10B981", hover_color="#059669")
        bot_core.is_paused_kompres = not bot_core.is_paused_kompres

    def start_bot_thread():
        save_config_data(entry_email, entry_password, combo_akun, combo_jenis, entry_batch, entry_folder, entry_harga,
                         entry_fototree, entry_deskripsi, entry_komp_sumber, entry_komp_tujuan, combo_jenis_komp,
                         entry_nama_app, entry_logo_path)
        email = entry_email.get().strip()
        password = entry_password.get().strip()
        jenis_media = combo_jenis.get()

        try:
            batch_size = int(entry_batch.get().strip())
            if batch_size <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Sistem", "Ukuran batch harus berupa angka positif.")
            return

        folder = entry_folder.get().strip()
        harga = entry_harga.get().strip()
        deskripsi = entry_deskripsi.get("1.0", tk.END).strip()
        fototree = entry_fototree.get().strip()

        if not email or not password or not folder or not harga or not deskripsi or not fototree:
            messagebox.showwarning("Sistem", "Harap isi semua konfigurasi dengan lengkap.")
            return

        btn_start.configure(state="disabled", fg_color=COLOR_BORDER, text_color=COLOR_MUTED)
        btn_pause.configure(state="normal")
        bot_core.is_paused = False
        bot_core.pause_event.set()
        btn_pause.configure(text="⏸ JEDA", fg_color="#F59E0B", hover_color="#D97706")
        txt_log.delete("1.0", tk.END)

        def log_ke_ui(pesan):
            root.after(0, lambda: [txt_log.insert(tk.END, pesan), txt_log.see(tk.END)])

        threading.Thread(target=bot_core.jalankan_bot,
                         args=(email, password, folder, harga, deskripsi, fototree, jenis_media, batch_size,
                               root, lbl_total_val, lbl_uploaded_val, lbl_failed_val, lbl_duplicate_val, btn_start, btn_pause, log_ke_ui),
                         daemon=True).start()

    def jalankan_proses_kompresi_mandiri():
        folder_sumber = entry_komp_sumber.get().strip()
        folder_tujuan = entry_komp_tujuan.get().strip()
        jenis_media = combo_jenis_komp.get()

        if not folder_sumber or not folder_tujuan:
            messagebox.showwarning("Sistem", "Direktori sumber/tujuan belum ditentukan.")
            return

        btn_jalankan_komp.configure(state="disabled", fg_color=COLOR_BORDER)
        btn_pause_komp.configure(state="normal")
        bot_core.is_paused_kompres = False
        bot_core.pause_event.set()
        btn_pause_komp.configure(text="⏸ JEDA", fg_color="#F59E0B")
        txt_log_komp.delete("1.0", tk.END)

        def log_kompres_ke_ui(pesan):
            root.after(0, lambda: [txt_log_komp.insert(tk.END, str(pesan) + "\n"), txt_log_komp.see(tk.END)])

        def worker():
            try:
                log_kompres_ke_ui(f"> Menginisialisasi pemindaian {jenis_media} di folder sumber...")
                file_list = bot_core.ambil_semua_media(folder_sumber, jenis_media)
                
                if not file_list:
                    log_kompres_ke_ui("> Error: File tidak ditemukan di sumber.")
                else:
                    total_file = len(file_list)
                    log_kompres_ke_ui(f"> Berhasil menemukan {total_file} file.")
                    log_kompres_ke_ui("> 🚀 MENGAKTIFKAN MODE TURBO (SATURASI 25%, METADATA & SIZE KECIL)...\n")
                    
                    import shutil
                    import concurrent.futures
                    from PIL import ImageEnhance
                    
                    def proses_satu_file(file_path, idx):
                        if bot_core.is_paused_kompres:
                            bot_core.pause_event.wait()
                            
                        nama_file = os.path.basename(file_path)
                        path_target = os.path.join(folder_tujuan, nama_file)
                        
                        try:
                            if jenis_media == "Foto":
                                with Image.open(file_path) as img:
                                    # 1. Ambil Metadata EXIF dan ICC Profile (Profil Warna) asli
                                    exif_data = img.info.get('exif')
                                    icc_profile = img.info.get('icc_profile')
                                    
                                    if img.mode in ("RGBA", "P"):
                                        img = img.convert("RGB")
                                    
                                    # 2. Naikkan saturasi sebanyak 25% (+25%)
                                    img = ImageEnhance.Color(img).enhance(1.25)
                                    
                                    # 3. Siapkan wadah parameter (Dictionary)
                                    # Kualitas 45 & optimize False menjamin proses sangat cepat dan ukuran file kecil
                                    save_kwargs = {"quality": 45, "optimize": False}
                                    
                                    # 4. Suntikkan kembali Metadata ke file yang baru
                                    if exif_data:
                                        save_kwargs["exif"] = exif_data
                                    if icc_profile:
                                        save_kwargs["icc_profile"] = icc_profile
                                        
                                    img.save(path_target, **save_kwargs)
                                    
                                ukuran_baru = os.path.getsize(path_target) / 1024
                                return f"✅ [{idx}/{total_file}] Sukses: {nama_file} ({ukuran_baru:.1f} KB)"
                            else:
                                shutil.copy2(file_path, path_target)
                                return f"✅ [{idx}/{total_file}] Tersalin: {nama_file}"
                        except Exception as e:
                            return f"❌ [{idx}/{total_file}] Gagal {nama_file}: {e}"

                    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                        futures = []
                        for i, path in enumerate(file_list):
                            futures.append(executor.submit(proses_satu_file, path, i + 1))
                            
                        for future in concurrent.futures.as_completed(futures):
                            log_kompres_ke_ui(future.result())

                    log_kompres_ke_ui("\n🏁 SELURUH PROSES KOMPRESI SELESAI DENGAN SANGAT CEPAT.")

            except Exception as e:
                log_kompres_ke_ui(f"> TERJADI KESALAHAN FATAL: {e}")
            finally:
                root.after(0, lambda: btn_jalankan_komp.configure(state="normal", fg_color=COLOR_PRIMARY, text_color=COLOR_BG))
                root.after(0, lambda: btn_pause_komp.configure(state="disabled"))

        threading.Thread(target=worker, daemon=True).start()
        
    # --- LAYOUT UTAMA ---
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    sidebar_container = ctk.CTkFrame(root, fg_color="transparent")
    sidebar_container.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
    sidebar_container.grid_rowconfigure(1, weight=1)

    sidebar = ctk.CTkFrame(sidebar_container, width=220, fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER, corner_radius=16)
    sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
    sidebar.grid_rowconfigure(4, weight=1) 

    logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    logo_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(25, 20))
    ctk.CTkLabel(logo_frame, text="Upload", font=font_logo, text_color=COLOR_PRIMARY).pack(side="left")
    ctk.CTkLabel(logo_frame, text="Manis", font=font_logo, text_color=COLOR_MUTED).pack(side="left")

    def select_menu(menu_name):
        for btn in [btn_upload, btn_kompres, btn_akun]:
            btn.configure(fg_color="transparent", text_color=COLOR_MUTED)
            
        frame_upload.grid_forget()
        frame_kompres.grid_forget()
        frame_akun.grid_forget()

        if menu_name == "upload":
            btn_upload.configure(fg_color="#18181B", text_color=COLOR_PRIMARY)
            frame_upload.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        elif menu_name == "kompres":
            btn_kompres.configure(fg_color="#18181B", text_color=COLOR_PRIMARY)
            frame_kompres.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        elif menu_name == "akun":
            btn_akun.configure(fg_color="#18181B", text_color=COLOR_PRIMARY)
            frame_akun.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)

    btn_upload = ctk.CTkButton(sidebar, text="Automasi Upload", font=font_btn, fg_color="transparent", text_color=COLOR_MUTED, hover_color="#18181B", corner_radius=8, anchor="w", height=40, command=lambda: select_menu("upload"))
    btn_upload.grid(row=1, column=0, padx=15, pady=4, sticky="ew")

    btn_kompres = ctk.CTkButton(sidebar, text="Kompresi Cerdas", font=font_btn, fg_color="transparent", text_color=COLOR_MUTED, hover_color="#18181B", corner_radius=8, anchor="w", height=40, command=lambda: select_menu("kompres"))
    btn_kompres.grid(row=2, column=0, padx=15, pady=4, sticky="ew")

    btn_akun = ctk.CTkButton(sidebar, text="Sistem & Akun", font=font_btn, fg_color="transparent", text_color=COLOR_MUTED, hover_color="#18181B", corner_radius=8, anchor="w", height=40, command=lambda: select_menu("akun"))
    btn_akun.grid(row=3, column=0, padx=15, pady=4, sticky="ew")

    # ==========================================================================
    # KARTU BAWAH KIRI (Kini memuat Gambar Logo Kustom + Teks Akun)
    # ==========================================================================
    user_card = ctk.CTkFrame(sidebar, fg_color="#121214", border_color=COLOR_BORDER, border_width=1, corner_radius=10)
    user_card.grid(row=5, column=0, sticky="ew", padx=15, pady=(0, 10))
    user_card.grid_columnconfigure(1, weight=1)
    
    # Label untuk menampung gambar/ikon logo di kiri bawah
    logo_bawah_lbl = ctk.CTkLabel(user_card, text="", width=32, height=32)
    logo_bawah_lbl.grid(row=0, column=0, padx=(10, 10), pady=10)
    
    user_email_lbl = ctk.CTkLabel(user_card, text="Belum Login", font=("Segoe UI", 11, "bold"), text_color=COLOR_PRIMARY, anchor="w")
    user_email_lbl.grid(row=0, column=1, sticky="ew", padx=(0, 10))

    # Variabel global penampung referensi gambar agar tidak terhapus Garbage Collector Python
    current_logo_image = [None]

    def update_sidebar_profile():
        email_aktif = combo_akun.get().strip() if combo_akun.get() else ""
        if email_aktif:
            teks_tampil = email_aktif if len(email_aktif) <= 15 else email_aktif[:12] + "..."
            user_email_lbl.configure(text=teks_tampil)
        else:
            user_email_lbl.configure(text="Belum Login")

    def terapkan_kustomisasi_tampilan_custom(entry_nama_app, entry_logo_path, root):
        nama_baru = entry_nama_app.get().strip()
        path_logo = entry_logo_path.get().strip()
        if nama_baru:
            root.title(nama_baru)
        
        if path_logo and os.path.exists(path_logo):
            try:
                # Ubah window icon utama
                if path_logo.lower().endswith('.ico'):
                    root.iconbitmap(path_logo)
                else:
                    img_tk = ImageTk.PhotoImage(Image.open(path_logo))
                    root.iconphoto(False, img_tk)
                
                # Tampilkan logo di bagian bawah kiri sidebar
                pil_img = Image.open(path_logo).resize((24, 24), Image.Resampling.LANCZOS)
                current_logo_image[0] = ImageTk.PhotoImage(pil_img)
                logo_bawah_lbl.configure(image=current_logo_image[0], text="")
            except Exception as e:
                print(f"Gagal memuat logo: {e}")
        else:
            # Fallback jika path kosong (menampilkan inisial teks kembali)
            logo_bawah_lbl.configure(image="", text="?")
        
        save_config_data()

    footer_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    footer_frame.grid(row=6, column=0, sticky="s", pady=(0, 25))
    dot = ctk.CTkFrame(footer_frame, width=8, height=8, corner_radius=4, fg_color="#10B981")
    dot.pack(side="left", padx=(0, 8))
    ctk.CTkLabel(footer_frame, text=f"v{bot_core.CURRENT_VERSION} - Online", font=("Segoe UI", 11), text_color=COLOR_MUTED).pack(side="left")

    def create_modern_input(parent, label_text, is_combobox=False, values=None, show=None, is_textbox=False):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(wrapper, text=label_text.upper(), font=("Segoe UI", 10, "bold"), text_color=COLOR_MUTED).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        safe_values = values if values is not None else []
        
        if is_combobox:
            widget = ctk.CTkComboBox(wrapper, values=safe_values, font=font_input, fg_color="#121214", border_color=COLOR_BORDER, border_width=1, corner_radius=6, button_color=COLOR_SURFACE, height=36)
        elif is_textbox:
            widget = ctk.CTkTextbox(wrapper, height=70, font=font_input, fg_color="#121214", border_color=COLOR_BORDER, border_width=1, corner_radius=6)
        else:
            widget = ctk.CTkEntry(wrapper, font=font_input, fg_color="#121214", border_color=COLOR_BORDER, border_width=1, corner_radius=6, height=36, show=show if show else "")
        widget.grid(row=1, column=0, sticky="ew")
        return widget, wrapper

    # =========================================================
    # FRAME 1: UPLOAD OTOMATIS
    # =========================================================
    frame_upload = ctk.CTkFrame(root, fg_color="transparent")
    frame_upload.grid_columnconfigure(1, weight=1)
    frame_upload.grid_rowconfigure(2, weight=1) 

    ctk.CTkLabel(frame_upload, text="Ringkasan Sistem", font=font_title, text_color=COLOR_PRIMARY).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

    stats_frame = ctk.CTkFrame(frame_upload, fg_color="transparent")
    stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
    stats_frame.grid_columnconfigure((0,1,2,3), weight=1)

    def create_stat_card(parent, title, color, col):
        card = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12, height=100)
        card.grid(row=0, column=col, sticky="ew", padx=6)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title.upper(), font=("Segoe UI", 10, "bold"), text_color=COLOR_MUTED).pack(anchor="w", padx=15, pady=(15, 0))
        val_lbl = ctk.CTkLabel(card, text="0", font=font_number, text_color=color)
        val_lbl.pack(anchor="w", padx=15, pady=(5, 10))
        return val_lbl

    lbl_total_val = create_stat_card(stats_frame, "Total Antrean", COLOR_PRIMARY, 0)
    lbl_uploaded_val = create_stat_card(stats_frame, "Sukses", "#10B981", 1)
    lbl_failed_val = create_stat_card(stats_frame, "Gagal", "#EF4444", 2)
    lbl_duplicate_val = create_stat_card(stats_frame, "Duplikat", "#F59E0B", 3)

    config_col = ctk.CTkFrame(frame_upload, fg_color="transparent", width=350)
    config_col.grid(row=2, column=0, sticky="nsew", pady=(0, 0), padx=(0, 10))
    terminal_col = ctk.CTkFrame(frame_upload, fg_color="transparent")
    terminal_col.grid(row=2, column=1, sticky="nsew", pady=(0, 0))
    terminal_col.grid_columnconfigure(0, weight=1)
    terminal_col.grid_rowconfigure(0, weight=1)
    terminal_col.grid_rowconfigure(1, weight=2)

    form_card = ctk.CTkFrame(config_col, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
    form_card.pack(fill="both", expand=True)
    ctk.CTkLabel(form_card, text="Konfigurasi Modul", font=("Segoe UI", 14, "bold"), text_color=COLOR_PRIMARY).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 5))

    combo_jenis, wrapper_jenis = create_modern_input(form_card, "Tipe Media", is_combobox=True, values=["Foto", "Video"])
    wrapper_jenis.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))
    
    entry_batch, wrapper_batch = create_modern_input(form_card, "Ukuran Batch")
    wrapper_batch.grid(row=1, column=1, sticky="ew", padx=15, pady=(5, 15))

    entry_harga, wrapper_harga = create_modern_input(form_card, "Tarif Dasar (IDR)")
    wrapper_harga.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
    
    entry_fototree, wrapper_ft = create_modern_input(form_card, "Label Fototree")
    wrapper_ft.grid(row=2, column=1, sticky="ew", padx=15, pady=(5, 15))

    wrapper_folder = ctk.CTkFrame(form_card, fg_color="transparent")
    wrapper_folder.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 15))
    ctk.CTkLabel(wrapper_folder, text="DIREKTORI SUMBER", font=("Segoe UI", 10, "bold"), text_color=COLOR_MUTED).pack(anchor="w", pady=(0, 5))
    f_row = ctk.CTkFrame(wrapper_folder, fg_color="transparent")
    f_row.pack(fill="x")
    entry_folder = ctk.CTkEntry(f_row, font=font_input, fg_color="#121214", border_color=COLOR_BORDER, border_width=1, corner_radius=6, height=36)
    entry_folder.pack(side="left", fill="x", expand=True, padx=(0, 8))
    ctk.CTkButton(f_row, text="Pilih", width=60, height=36, corner_radius=6, fg_color="#27272A", hover_color="#3F3F46", text_color=COLOR_PRIMARY, command=lambda: cari_direktori(entry_folder)).pack(side="left")

    entry_deskripsi, wrapper_desc = create_modern_input(form_card, "Deskripsi Metadata", is_textbox=True)
    wrapper_desc.grid(row=4, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 15))

    btn_box = ctk.CTkFrame(form_card, fg_color="transparent")
    btn_box.grid(row=5, column=0, columnspan=2, sticky="ew", padx=15, pady=(10, 20))
    btn_start = ctk.CTkButton(btn_box, text="EKSEKUSI", font=font_btn, height=40, fg_color=COLOR_PRIMARY, hover_color="#E4E4E7", text_color=COLOR_BG, command=start_bot_thread)
    btn_start.pack(side="left", fill="x", expand=True, padx=(0, 8))
    btn_pause = ctk.CTkButton(btn_box, text="JEDA", font=font_btn, height=40, width=90, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, hover_color="#27272A", state="disabled", command=lambda: toggle_pause(btn_pause))
    btn_pause.pack(side="left")

    # KARTU GRAFIK JARINGAN
    graph_card = ctk.CTkFrame(terminal_col, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
    graph_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
    graph_card.grid_columnconfigure(0, weight=1)
    graph_card.grid_rowconfigure(1, weight=1)

    speed_header = ctk.CTkFrame(graph_card, fg_color="transparent")
    speed_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))
    ctk.CTkLabel(speed_header, text="Network Activity", font=("Segoe UI", 12, "bold"), text_color=COLOR_PRIMARY).pack(side="left")
    lbl_ul_speed = ctk.CTkLabel(speed_header, text="UP: 0.00 KB/s", font=("Consolas", 12, "bold"), text_color=COLOR_UL)
    lbl_ul_speed.pack(side="right", padx=(15, 0))
    lbl_dl_speed = ctk.CTkLabel(speed_header, text="DL: 0.00 KB/s", font=("Consolas", 12, "bold"), text_color=COLOR_DL)
    lbl_dl_speed.pack(side="right")

    MAX_LEN = 60
    x_data = deque([i for i in range(MAX_LEN)], maxlen=MAX_LEN)
    dl_data = deque([0] * MAX_LEN, maxlen=MAX_LEN)
    ul_data = deque([0] * MAX_LEN, maxlen=MAX_LEN)

    fig, ax = plt.subplots(1, 1, figsize=(5, 2.5), dpi=100)
    fig.patch.set_facecolor(COLOR_SURFACE)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.15)

    line_dl, = ax.plot(x_data, dl_data, color=COLOR_DL, linewidth=1.5, label="Download")
    line_ul, = ax.plot(x_data, ul_data, color=COLOR_UL, linewidth=1.5, label="Upload")
    
    ax.set_facecolor(COLOR_SURFACE)
    ax.tick_params(colors=COLOR_MUTED, labelsize=8)
    ax.spines['bottom'].set_color(COLOR_BORDER)
    ax.spines['left'].set_color(COLOR_BORDER)
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.grid(axis='y', color=COLOR_BORDER, linestyle='--', alpha=0.3)
    ax.set_xlim(0, MAX_LEN - 1)
    ax.set_ylim(0, 100)
    ax.set_xticks([]) 

    canvas = FigureCanvasTkAgg(fig, master=graph_card)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    term_card = ctk.CTkFrame(terminal_col, fg_color="#0A0A0C", border_color=COLOR_BORDER, border_width=1, corner_radius=12)
    term_card.grid(row=1, column=0, sticky="nsew")
    term_card.pack_propagate(False)
    
    term_header = ctk.CTkFrame(term_card, fg_color="transparent", height=30)
    term_header.pack(fill="x", padx=15, pady=(10, 0))
    term_header.pack_propagate(False)
    for c in ["#EF4444", "#F59E0B", "#10B981"]:
        ctk.CTkFrame(term_header, width=10, height=10, corner_radius=5, fg_color=c).pack(side="left", padx=3)
    ctk.CTkLabel(term_header, text="bash - app_console", font=("Consolas", 10), text_color="#52525B").pack(side="left", padx=15)
    
    txt_log = ctk.CTkTextbox(term_card, fg_color="transparent", text_color="#A1A1AA", font=("Consolas", 12))
    txt_log.pack(fill="both", expand=True, padx=15, pady=(5, 15))

    def update_network_graph():
        try:
            current_net_io = psutil.net_io_counters()
            if not hasattr(update_network_graph, 'last_io'):
                update_network_graph.last_io = current_net_io
                
            bytes_sent = current_net_io.bytes_sent - update_network_graph.last_io.bytes_sent
            bytes_recv = current_net_io.bytes_recv - update_network_graph.last_io.bytes_recv
            update_network_graph.last_io = current_net_io

            ul_kbs = bytes_sent / 1024.0
            dl_kbs = bytes_recv / 1024.0

            lbl_ul_speed.configure(text=f"UP: {ul_kbs:.1f} KB/s")
            lbl_dl_speed.configure(text=f"DL: {dl_kbs:.1f} KB/s")

            ul_data.append(ul_kbs)
            dl_data.append(dl_kbs)

            line_dl.set_ydata(dl_data)
            line_ul.set_ydata(ul_data)

            max_val = max(max(dl_data), max(ul_data))
            ax.set_ylim(0, max(max_val * 1.2, 100))

            canvas.draw()
        except Exception:
            pass
        root.after(1000, update_network_graph)

    root.after(1000, update_network_graph)


    # =========================================================
    # FRAME 2: KOMPRESI FILE
    # =========================================================
    frame_kompres = ctk.CTkFrame(root, fg_color="transparent")
    frame_kompres.grid_columnconfigure(0, weight=1)
    frame_kompres.grid_rowconfigure(2, weight=1)

    ctk.CTkLabel(frame_kompres, text="Mesin Kompresi", font=font_title, text_color=COLOR_PRIMARY).grid(row=0, column=0, sticky="w", pady=(0, 20))

    komp_card = ctk.CTkFrame(frame_kompres, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
    komp_card.grid(row=1, column=0, sticky="ew", pady=(0, 20))
    komp_card.grid_columnconfigure(0, weight=1)

    combo_jenis_komp, wrap_kj = create_modern_input(komp_card, "Format Engine", is_combobox=True, values=["Foto", "Video"])
    wrap_kj.grid(row=0, column=0, sticky="ew", padx=15, pady=(5, 15))
    
    def create_dir_input(parent, label, row):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=0, sticky="ew", padx=15, pady=(5, 15))
        ctk.CTkLabel(wrapper, text=label, font=("Segoe UI", 10, "bold"), text_color=COLOR_MUTED).pack(anchor="w", pady=(0, 5))
        f_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        f_row.pack(fill="x")
        entry = ctk.CTkEntry(f_row, font=font_input, fg_color="#121214", border_color=COLOR_BORDER, border_width=1, corner_radius=6, height=36)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(f_row, text="Pilih", width=60, height=36, corner_radius=6, fg_color="#27272A", text_color=COLOR_PRIMARY, command=lambda: cari_direktori(entry)).pack(side="left")
        return entry

    entry_komp_sumber = create_dir_input(komp_card, "ROOT DIRECTORY (SUMBER)", 1)
    entry_komp_tujuan = create_dir_input(komp_card, "OUTPUT DIRECTORY (TUJUAN)", 2)

    btn_box_k = ctk.CTkFrame(komp_card, fg_color="transparent")
    btn_box_k.grid(row=3, column=0, sticky="ew", padx=15, pady=(10, 20))
    btn_jalankan_komp = ctk.CTkButton(btn_box_k, text="MULAI KOMPRESI", font=font_btn, height=40, fg_color=COLOR_PRIMARY, text_color=COLOR_BG, hover_color="#E4E4E7", command=jalankan_proses_kompresi_mandiri)
    btn_jalankan_komp.pack(side="left", fill="x", expand=True, padx=(0, 8))
    btn_pause_komp = ctk.CTkButton(btn_box_k, text="JEDA", font=font_btn, height=40, width=90, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, hover_color="#27272A", state="disabled", command=lambda: toggle_pause_kompres(btn_pause_komp))
    btn_pause_komp.pack(side="left")

    term_card_k = ctk.CTkFrame(frame_kompres, fg_color="#0A0A0C", border_color=COLOR_BORDER, border_width=1, corner_radius=12)
    term_card_k.grid(row=2, column=0, sticky="nsew")
    txt_log_komp = ctk.CTkTextbox(term_card_k, fg_color="transparent", text_color="#A1A1AA", font=("Consolas", 12))
    txt_log_komp.pack(fill="both", expand=True, padx=15, pady=15)


    # =========================================================
    # FRAME 3: AKUN & PENGATURAN
    # =========================================================
    frame_akun = ctk.CTkFrame(root, fg_color="transparent")
    frame_akun.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(frame_akun, text="Sistem & Keamanan", font=font_title, text_color=COLOR_PRIMARY).grid(row=0, column=0, sticky="w", pady=(0, 20))

    setting_grid = ctk.CTkFrame(frame_akun, fg_color="transparent")
    setting_grid.grid(row=1, column=0, sticky="nsew")
    setting_grid.grid_columnconfigure((0,1), weight=1)

    cred_card = ctk.CTkFrame(setting_grid, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
    cred_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    ctk.CTkLabel(cred_card, text="Manajemen Kredensial", font=("Segoe UI", 14, "bold"), text_color=COLOR_PRIMARY).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
    
    combo_akun, wrap_akun = create_modern_input(cred_card, "Pilih Akun", is_combobox=True)
    wrap_akun.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))
    
    def on_akun_changed(choice):
        on_pilih_akun(choice, combo_akun, entry_email, entry_password)
        update_sidebar_profile()

    combo_akun.configure(command=on_akun_changed)
    
    entry_email, wrap_email = create_modern_input(cred_card, "Identifier (Email)")
    wrap_email.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
    
    entry_password, wrap_pass = create_modern_input(cred_card, "Kata Sandi", show="●")
    wrap_pass.grid(row=3, column=0, sticky="ew", padx=15, pady=(5, 15))

    def action_simpan():
        simpan_akun(entry_email, entry_password, combo_akun)
        update_sidebar_profile()

    def action_hapus():
        hapus_akun(entry_email, entry_password, combo_akun)
        update_sidebar_profile()

    btn_akun_box = ctk.CTkFrame(cred_card, fg_color="transparent")
    btn_akun_box.grid(row=4, column=0, sticky="ew", padx=15, pady=(10, 20))
    ctk.CTkButton(btn_akun_box, text="SIMPAN", font=font_btn, height=36, fg_color=COLOR_PRIMARY, text_color=COLOR_BG, hover_color="#E4E4E7", command=action_simpan).pack(side="left", fill="x", expand=True, padx=(0, 8))
    ctk.CTkButton(btn_akun_box, text="HAPUS", font=font_btn, height=36, fg_color="transparent", border_color="#EF4444", border_width=1, text_color="#EF4444", hover_color="#450a0a", command=action_hapus).pack(side="left", fill="x", expand=True)

    ui_card = ctk.CTkFrame(setting_grid, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
    ui_card.grid(row=0, column=1, sticky="nsew")
    ctk.CTkLabel(ui_card, text="Personalisasi Antarmuka", font=("Segoe UI", 14, "bold"), text_color=COLOR_PRIMARY).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

    entry_nama_app, wrap_nama = create_modern_input(ui_card, "Sematkan Judul Window")
    wrap_nama.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))
    entry_nama_app.insert(0, f"Upload Manis V{bot_core.CURRENT_VERSION}")
    
    wrapper_logo = ctk.CTkFrame(ui_card, fg_color="transparent")
    wrapper_logo.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
    ctk.CTkLabel(wrapper_logo, text="PATH LOGO IKON", font=("Segoe UI", 10, "bold"), text_color=COLOR_MUTED).pack(anchor="w", pady=(0, 5))
    l_row = ctk.CTkFrame(wrapper_logo, fg_color="transparent")
    l_row.pack(fill="x")
    entry_logo_path = ctk.CTkEntry(l_row, font=font_input, fg_color="#121214", border_color=COLOR_BORDER, border_width=1, corner_radius=6, height=36)
    entry_logo_path.pack(side="left", fill="x", expand=True, padx=(0, 8))
    ctk.CTkButton(l_row, text="Pilih", width=60, height=36, corner_radius=6, fg_color="#27272A", text_color=COLOR_PRIMARY, command=lambda: cari_file_logo(entry_logo_path)).pack(side="left")

    def action_terapkan_ui():
        terapkan_kustomisasi_tampilan_custom(entry_nama_app, entry_logo_path, root)

    ctk.CTkButton(ui_card, text="TERAPKAN TEMA", font=font_btn, height=36, fg_color="#27272A", hover_color="#3F3F46", text_color=COLOR_PRIMARY, command=action_terapkan_ui).grid(row=3, column=0, sticky="ew", padx=15, pady=(10, 20))

    # --- PENGISIAN DATA AWAL ---
    if konfig_termuat:
        try:
            if "accounts" in konfig_termuat: bot_core.saved_accounts.update(konfig_termuat["accounts"])
            perbarui_combobox_akun(combo_akun, entry_email, entry_password, konfig_termuat.get("last_account"))
            combo_jenis.set(konfig_termuat.get("jenis", "Foto"))
            entry_batch.delete(0, tk.END); entry_batch.insert(0, konfig_termuat.get("batch", "50"))
            entry_folder.delete(0, tk.END); entry_folder.insert(0, konfig_termuat.get("folder", ""))
            entry_harga.delete(0, tk.END); entry_harga.insert(0, konfig_termuat.get("harga", "50000"))
            entry_fototree.delete(0, tk.END); entry_fototree.insert(0, konfig_termuat.get("fototree", ""))
            entry_deskripsi.delete("1.0", tk.END); entry_deskripsi.insert("1.0", konfig_termuat.get("deskripsi", ""))
            entry_komp_sumber.delete(0, tk.END); entry_komp_sumber.insert(0, konfig_termuat.get("komp_sumber", ""))
            entry_komp_tujuan.delete(0, tk.END); entry_komp_tujuan.insert(0, konfig_termuat.get("komp_tujuan", ""))
            combo_jenis_komp.set(konfig_termuat.get("komp_jenis", "Foto"))

            saved_app_name = konfig_termuat.get("app_name", "")
            if saved_app_name:
                entry_nama_app.delete(0, tk.END); entry_nama_app.insert(0, saved_app_name); root.title(saved_app_name)
            saved_logo = konfig_termuat.get("logo_path", "")
            if saved_logo:
                entry_logo_path.delete(0, tk.END); entry_logo_path.insert(0, saved_logo)
                terapkan_kustomisasi_tampilan_custom(entry_nama_app, entry_logo_path, root)
        except Exception:
            pass

    update_sidebar_profile()
    select_menu("upload")

    root.protocol("WM_DELETE_WINDOW", lambda: (save_config_data(entry_email, entry_password, combo_akun, combo_jenis, entry_batch, entry_folder, entry_harga, entry_fototree, entry_deskripsi, entry_komp_sumber, entry_komp_tujuan, combo_jenis_komp, entry_nama_app, entry_logo_path), root.destroy()))

# ======================================================================
# INISIALISASI LISENSI LAYAR 
# ======================================================================
def show_license_screen(root, hwid, konfig_termuat):
    ctk.set_appearance_mode("dark")
    root.configure(fg_color="#000000") 
    root.title("Aktivasi Lisensi")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    frame = ctk.CTkFrame(root, corner_radius=16, width=450, fg_color="#0A0A0A", border_width=1, border_color="#27272A")
    frame.grid(row=0, column=0)
    frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(frame, text="Autentikasi Diperlukan", font=("Segoe UI Variable Display", 22, "bold"), text_color="#FFFFFF").grid(row=0, column=0, pady=(40, 5))
    ctk.CTkLabel(frame, text="Sistem ini dilindungi oleh enkripsi lisensi HWID.", font=("Segoe UI", 12), text_color="#A1A1AA").grid(row=1, column=0, pady=5)

    hwid_box = ctk.CTkFrame(frame, fg_color="#121214", border_width=1, border_color="#27272A", corner_radius=8)
    hwid_box.grid(row=2, column=0, pady=(25, 10), padx=40, sticky="ew")
    ctk.CTkLabel(hwid_box, text="HARDWARE ID ANDA", font=("Segoe UI", 10, "bold"), text_color="#71717A").pack(pady=(10, 0))
    hwid_entry = ctk.CTkEntry(hwid_box, width=300, justify="center", font=("Consolas", 14), fg_color="transparent", text_color="#3B82F6", border_width=0)
    hwid_entry.pack(pady=(5, 10))
    hwid_entry.insert(0, hwid)
    hwid_entry.configure(state="readonly")

    ctk.CTkLabel(frame, text="KUNCI LISENSI", font=("Segoe UI", 10, "bold"), text_color="#71717A").grid(row=3, column=0, pady=(15, 0))
    key_entry = ctk.CTkEntry(frame, width=370, justify="center", height=45, font=("Consolas", 14), fg_color="#121214", border_width=1, border_color="#3F3F46", corner_radius=8)
    key_entry.grid(row=4, column=0, pady=(5, 15))

    lbl_status = ctk.CTkLabel(frame, text="", font=("Segoe UI", 12))
    lbl_status.grid(row=5, column=0)

    def aktivasi():
        k = key_entry.get().strip()
        is_valid, pesan = bot_core.verify_license(k, hwid)
        if is_valid:
            bot_core.app_license_key = k
            lbl_status.configure(text="Akses Diberikan. Memuat sistem...", text_color="#10B981") 
            root.update()
            time.sleep(1.5)
            data = {"license_key": k}
            with open(bot_core.CONFIG_FILE, "w") as f:
                json.dump(data, f)
            show_main_app(root, konfig_termuat)
        else:
            lbl_status.configure(text=f"Akses Ditolak: {pesan}", text_color="#EF4444") 

    ctk.CTkButton(frame, text="VERIFIKASI & MASUK", font=("Segoe UI", 13, "bold"), height=45, width=370, corner_radius=8, fg_color="#FFFFFF", hover_color="#E4E4E7", text_color="#000000", command=aktivasi).grid(row=6, column=0, pady=(10, 40))

# ======================================================================
# PROGRAM UTAMA
# ======================================================================
def main():
    root = ctk.CTk()
    root.geometry("1100x800") 
    root.minsize(1050, 750)

    hwid = bot_core.get_hwid()
    data_konfigurasi = {}

    if os.path.exists(bot_core.CONFIG_FILE):
        try:
            with open(bot_core.CONFIG_FILE, "r") as f:
                data_konfigurasi = json.load(f)
                bot_core.app_license_key = data_konfigurasi.get("license_key", "")
        except Exception:
            pass

    is_valid, msg = bot_core.verify_license(bot_core.app_license_key, hwid)

    if is_valid:
        show_main_app(root, data_konfigurasi)
    else:
        show_license_screen(root, hwid, data_konfigurasi)

    root.mainloop()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()