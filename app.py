from flask import Flask, render_template, request
from pytube import YouTube
from moviepy.editor import VideoFileClip, clips_array
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
import os
import time
import psutil
import subprocess

app = Flask(__name__)

def download_and_combine_youtube_videos(youtube_url_1, youtube_url_2, output_path, client_secrets_file, video_title, video_description):
    video_path_1 = None
    video_path_2 = None
    clip1 = None
    clip2 = None

    try:

        youtube_video_1 = YouTube(youtube_url_1)
        video_path_1 = youtube_video_1.streams.filter(file_extension="mp4").first().download()

        youtube_video_2 = YouTube(youtube_url_2)
        video_path_2 = youtube_video_2.streams.filter(file_extension="mp4").first().download()

        clip1 = VideoFileClip(video_path_1)
        clip2 = VideoFileClip(video_path_2)

        min_duration = min(clip1.duration, clip2.duration)
        clip1 = clip1.set_duration(min_duration)
        clip2 = clip2.set_duration(min_duration)

        clip2 = clip2.set_audio(None)

        final_clip = clips_array([[clip1], [clip2]])

        final_clip = final_clip.crop(y1=0, y2=1920)

        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

        print(f"Video successfully created at {output_path}")

        publish_video_to_youtube(output_path, client_secrets_file, video_title, video_description)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if clip1 is not None:
            clip1.close()
        if clip2 is not None:
            clip2.close()

        time.sleep(3) 

        try:
            for file in [video_path_1, video_path_2]:
                if file is not None and os.path.exists(file):
                    process = psutil.Process(os.getpid())
                    for item in process.open_files():
                        if item.path == file:
                            subprocess.run(['taskkill', '/F', '/T', '/PID', str(item.pid)])
        except Exception as e:
            print(f"Error terminating processes: {e}")

        try:
            if video_path_1 is not None and os.path.exists(video_path_1) and video_path_1 != output_path:
                os.remove(video_path_1)
        except Exception as e:
            print(f"Error deleting file {video_path_1}: {e}")

        try:
            if video_path_2 is not None and os.path.exists(video_path_2) and video_path_2 != output_path:
                os.remove(video_path_2)
        except Exception as e:
            print(f"Error deleting file {video_path_2}: {e}")

def publish_video_to_youtube(output_path, client_secrets_file, video_title, video_description):
    try:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, ["https://www.googleapis.com/auth/youtube.upload"])
        credentials = flow.run_local_server(port=0)

        youtube = build("youtube", "v3", credentials=credentials)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "description": video_description,
                    "title": video_title,
                    "tags": ["YouTube Shorts"],
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": "public"
                }
            },
            media_body=MediaFileUpload(output_path)
        )

        response = request.execute()

        print(f"Video successfully published to YouTube. Video ID: {response['id']}")

    except Exception as e:
        print(f"Error publishing video to YouTube: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    youtube_url_1 = request.form['youtube_url_1']
    youtube_url_2 = request.form['youtube_url_2']
    video_title = request.form['video_title'] 
    video_description = request.form['video_description'] 

    output_path = "C:\\MyApps\\videomaker\\video\\output.mp4"
    client_secrets_file = "C:\\MyApps\\videomaker\\client_secret.json"

    download_and_combine_youtube_videos(youtube_url_1, youtube_url_2, output_path, client_secrets_file, video_title, video_description)

    return render_template('result.html')


if __name__ == '__main__':
    app.run(debug=True)
