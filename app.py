import os
import asyncio
import threading
from flask import Flask, request, render_template
import cloudinary
import cloudinary.uploader
import discord
from discord.ext import commands

app = Flask(__name__)

# Cloudinaryの設定
cloudinary.config(
    cloud_name=os.getenv('CLOUD_NAME'),
    api_key=os.getenv('API_KEY'),
    api_secret=os.getenv('API_SECRET')
)

# Discordボットの設定
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = 1244248370307010654  # 送信先のチャンネルID

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """動画を受け取り、Cloudinaryにアップロードし、Discordに送信"""
    if 'file' not in request.files:
        return 'ファイルが見つかりませんでした。'
    file = request.files['file']
    if file.filename == '':
        return 'ファイル名が空です。'

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # 非同期で動画をアップロード・送信
    threading.Thread(target=process_and_send, args=(file_path,)).start()

    return render_template('upload.html', message='ファイルがアップロードされました！')

def process_and_send(file_path):
    """動画をCloudinaryにアップロードし、Discordに送信"""
    upload_result = cloudinary.uploader.upload(
        file_path,
        resource_type='video',
        eager=[{'width': 800, 'height': 600, 'crop': 'limit'}]
    )

    # 圧縮後の動画URL
    compressed_video_url = upload_result['eager'][0]['secure_url']

    # Discordへ送信
    asyncio.create_task(send_to_discord(compressed_video_url))

async def send_to_discord(video_url):
    """Discordに動画のURLを送信"""
    async with bot:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(CHANNEL_ID)
        await channel.send(video_url)

if __name__ == '__main__':
    bot.loop.create_task(app.run(debug=True, use_reloader=False))
    bot.run(TOKEN)
