import tkinter as tk
from tkinter import filedialog, messagebox
import instaloader
import requests
import os
import re
import sys
import subprocess  # ✅ 폴더 열기 기능 추가
from yt_dlp import YoutubeDL
from threading import Thread

# 현재 실행파일 위치 찾기
if getattr(sys, 'frozen', False):  # .exe 실행 중
    exe_dir = os.path.dirname(sys.executable)
else:
    exe_dir = os.path.dirname(os.path.abspath(__file__))  # .py 실행 중

ffmpeg_path = os.path.join(exe_dir, "ffmpeg.exe")  # FFmpeg 경로 지정

# GUI 상태 업데이트 함수 (Tkinter 메인 스레드에서 실행)
def update_status_label(text):
    status_label.after(0, lambda: status_label.config(text=text))

# 플랫폼별 다운로드 함수 정의
def download_instagram(url, save_folder):
    try:
        update_status_label("다운로드 중...")  # ✅ 다운로드 중 상태 표시
        L = instaloader.Instaloader()
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        caption = post.caption or "제목없음"
        title = caption.strip().split('\n')[0]
        title = re.sub(r'[\\/*?:"<>|]', "", title)[:50].strip()

        video_url = post.video_url
        response = requests.get(video_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        filepath = os.path.join(save_folder, f"{title}.mp4")
        downloaded = 0

        with open(filepath, "wb") as file:
            for data in response.iter_content(block_size):
                downloaded += len(data)
                file.write(data)
                percent = (downloaded / total_size) * 100
                update_status_label(f"다운로드 중... {percent:.1f}%")

        update_status_label(f"✅ 다운로드 완료! 저장 위치: {filepath}")  # ✅ 다운로드 완료 후 메시지 표시
    except Exception as e:
        update_status_label(f"❌ 다운로드 실패: {str(e)}")

# 유튜브 & 틱톡 다운로드 (MP4 + H.264 코덱)
def download_yt_tiktok(url, save_folder):
    def hook(d):
        if d['status'] == 'downloading':
            percent = d['_percent_str'].strip()
            update_status_label(f"다운로드 중... {percent}")
        elif d['status'] == 'finished':
            update_status_label(f"✅ 다운로드 완료! 저장 위치: {d['filename']}")  # ✅ 다운로드 완료 후 메시지 표시

    try:
        update_status_label("다운로드 중...")  # ✅ 다운로드 시작 시 상태 업데이트
        ydl_opts = {
            'outtmpl': os.path.join(save_folder, '%(title).50s.%(ext)s'),
            'format': 'bv*[ext=mp4][vcodec^=avc1]+ba[ext=m4a]/b[ext=mp4]',  # ✅ H.264(avc1) 코덱 강제
            'merge_output_format': 'mp4',  # ✅ 최종 파일 MP4 병합
            'ffmpeg_location': ffmpeg_path,
            'progress_hooks': [hook]
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        update_status_label(f"❌ 다운로드 실패: {str(e)}")

# 플랫폼 감지 함수
def detect_platform(url):
    if 'instagram.com' in url:
        return 'instagram'
    elif 'tiktok.com' in url:
        return 'tiktok'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    else:
        return None

# 다운로드 버튼 클릭 시 실행 함수
def start_download():
    url = url_entry.get()
    save_folder = folder_entry.get().strip()

    if not url:
        messagebox.showerror("오류", "링크를 입력해주세요.")
        return

    if not save_folder:
        save_folder = os.getcwd()
    save_folder = os.path.abspath(save_folder)
    os.makedirs(save_folder, exist_ok=True)

    platform = detect_platform(url)

    download_button.config(state=tk.DISABLED)  # ✅ 다운로드 중 버튼 비활성화
    update_status_label("다운로드 시작 중...")

    if platform == 'instagram':
        Thread(target=lambda: download_instagram(url, save_folder)).start()
    elif platform in ('tiktok', 'youtube'):
        Thread(target=lambda: download_yt_tiktok(url, save_folder)).start()
    else:
        messagebox.showerror("오류", "지원하지 않는 플랫폼이거나 잘못된 링크입니다.")
        download_button.config(state=tk.NORMAL)
        return

# 폴더 선택 함수
def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_entry.delete(0, "end")
        folder_entry.insert(0, folder_selected)

# ✅ 폴더 열기 함수
def open_folder():
    folder_path = folder_entry.get().strip()
    if not folder_path:
        folder_path = os.getcwd()  # 기본 폴더 = 현재 디렉토리
    os.startfile(folder_path)  # Windows에서 폴더 열기

# GUI 구성
app = tk.Tk()
app.title("릴스·틱톡·유튜브 다운로더")
app.geometry("600x230")

url_label = tk.Label(app, text="영상 링크를 입력하세요.")
url_label.pack(pady=(10, 0))

url_entry = tk.Entry(app, width=65)
url_entry.pack(pady=5)

folder_frame = tk.Frame(app)
folder_frame.pack(pady=5)

folder_label = tk.Label(folder_frame, text="저장경로:")
folder_label.pack(side="left", padx=5)

folder_entry = tk.Entry(folder_frame, width=35)  # ✅ 입력창 너비 조정
folder_entry.pack(side="left", padx=5)

folder_button = tk.Button(folder_frame, text="선택", command=browse_folder)
folder_button.pack(side="left", padx=5)

# ✅ 폴더 열기 버튼 추가
open_folder_button = tk.Button(folder_frame, text="폴더 열기", command=open_folder)
open_folder_button.pack(side="left", padx=5)

# 다운로드 버튼
download_button = tk.Button(app, text="다운로드", command=start_download, width=20, bg="#4a90e2", fg="white")
download_button.pack(pady=10)

# 진행 상태 라벨
status_label = tk.Label(app, text="", fg="green")
status_label.pack(pady=5)

app.mainloop()
