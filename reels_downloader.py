import os
import re
import requests
import yt_dlp
import instaloader

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_instagram(url):
    """ 인스타그램 영상 다운로드 """
    try:
        L = instaloader.Instaloader()
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        title = (post.caption or "제목없음").strip().split('\n')[0]
        title = re.sub(r'[\\/*?:"<>|]', "", title)[:50].strip()

        video_url = post.video_url
        response = requests.get(video_url, stream=True)
        filepath = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp4")

        with open(filepath, "wb") as file:
            for data in response.iter_content(1024):
                file.write(data)

        return f"✅ 다운로드 완료! 파일: {filepath}"
    except Exception as e:
        return f"❌ 오류 발생: {e}"

def download_yt_tiktok(url):
    """ 유튜브 & 틱톡 영상 다운로드 (H.264 MP4) """
    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title).50s.%(ext)s'),
            'format': 'bv*[ext=mp4][vcodec^=avc1]+ba[ext=m4a]/b[ext=mp4]',
            'merge_output_format': 'mp4'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return "✅ 다운로드 완료!"
    except Exception as e:
        return f"❌ 오류 발생: {e}"

def detect_platform(url):
    """ URL을 기반으로 플랫폼 감지 """
    if 'instagram.com' in url:
        return 'instagram'
    elif 'tiktok.com' in url:
        return 'tiktok'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    else:
        return None

def start_download(url):
    """ Flask에서 호출 가능한 다운로드 함수 """
    platform = detect_platform(url)
    if platform == 'instagram':
        return download_instagram(url)
    elif platform in ('tiktok', 'youtube'):
        return download_yt_tiktok(url)
    else:
        return "❌ 지원하지 않는 플랫폼입니다."
