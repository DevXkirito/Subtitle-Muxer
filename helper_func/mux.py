from config import Config
import time
import re
import asyncio
import os
import json
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

progress_pattern = re.compile(r'(frame|fps|size|time|bitrate|speed)\s*\=\s*(\S+)')

def parse_progress(line):
    return {key: value for key, value in progress_pattern.findall(line)}

async def readlines(stream):
    pattern = re.compile(br'[\r\n]+')
    data = bytearray()
    while not stream.at_eof():
        lines = pattern.split(data)
        data[:] = lines.pop(-1)
        for line in lines:
            yield line
        data.extend(await stream.read(1024))

async def safe_edit_message(msg, text):
    try:
        await msg.edit(text)
    except Exception as e:
        if "messages.EditMessage" in str(e):
            await asyncio.sleep(10)
            try:
                await msg.edit(text)
            except Exception as retry_error:
                print(f"Retry failed: {retry_error}")

async def read_stderr(start, msg, process):
    error_log = []
    last_edit_time = time.time()

    async for line in readlines(process.stderr):
        line = line.decode('utf-8')
        error_log.append(line)
        progress = parse_progress(line)
        
        if progress and (time.time() - last_edit_time >= 10):
            text = f"🔄 **Processing...**\nSize: {progress.get('size', 'N/A')}\nTime: {progress.get('time', 'N/A')}\nSpeed: {progress.get('speed', 'N/A')}"
            await safe_edit_message(msg, text)
            last_edit_time = time.time()

    return "\n".join(error_log)

async def generate_screenshots(video_path, num_screenshots=5):
    """Generate multiple screenshots at fixed intervals."""
    screenshot_paths = []

    for i in range(num_screenshots):
        timestamp = i * 10  # Take a screenshot every 10 seconds
        screenshot_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_screenshot_{i+1}.jpg"
        screenshot_path = os.path.join(Config.DOWNLOAD_DIR, screenshot_filename)

        command = [
            'ffmpeg', '-hide_banner', '-ss', str(timestamp), '-i', video_path,
            '-frames:v', '1', '-q:v', '2', '-y', screenshot_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0 and os.path.exists(screenshot_path):
            screenshot_paths.append(screenshot_path)
        else:
            print(f"⚠️ Screenshot {i+1} failed: {stderr.decode()}")

    return screenshot_paths

async def send_screenshots(msg, screenshots):
    """Send screenshots as images instead of URL buttons."""
    if screenshots:
        await msg.reply_text("📸 **Screenshots Generated:**")
        for screenshot in screenshots:
            await msg.reply_photo(screenshot)

async def softmux_vid(vid_filename, sub_filename, msg):
    start = time.time()
    vid = os.path.join(Config.DOWNLOAD_DIR, vid_filename)
    sub = os.path.join(Config.DOWNLOAD_DIR, sub_filename)
    output = f"{os.path.splitext(vid_filename)[0]}_muxed.mkv"
    out_location = os.path.join(Config.DOWNLOAD_DIR, output)
    sub_ext = sub_filename.split('.')[-1]

    command = [
        'ffmpeg', '-hide_banner', '-i', vid, '-i', sub,
        '-map', '1:0', '-map', '0', '-disposition:s:0', 'default',
        '-c:v', 'copy', '-c:a', 'copy', '-c:s', sub_ext,
        '-y', out_location
    ]

    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    error_output = await read_stderr(start, msg, process)
    await process.wait()

    if process.returncode == 0:
        await safe_edit_message(msg, f'✅ **Muxing Completed!**\n⏳ Time: {round(time.time() - start)}s')

        screenshots = await generate_screenshots(out_location)
        await send_screenshots(msg, screenshots)

        return output
    else:
        await safe_edit_message(msg, f'❌ **Muxing Failed!**\n\nError:\n```{error_output}```')
        return False

async def hardmux_vid(vid_filename, sub_filename, msg):
    start = time.time()
    vid = os.path.join(Config.DOWNLOAD_DIR, vid_filename)
    sub = os.path.join(Config.DOWNLOAD_DIR, sub_filename)
    output = f"{os.path.splitext(vid_filename)[0]}_hardmuxed.mp4"
    out_location = os.path.join(Config.DOWNLOAD_DIR, output)

    font_path = os.path.join(os.getcwd(), "fonts", "HelveticaRounded-Bold.ttf")
    if not os.path.exists(font_path):
        await safe_edit_message(msg, "❌ Font not found! Place 'HelveticaRounded-Bold.ttf' in 'fonts' folder.")
        return False

    formatted_sub = "'{}'".format(sub.replace(":", "\\:")) if " " in sub else sub.replace(":", "\\:")
    
    command = [
        'ffmpeg', '-hide_banner', '-i', vid,
        '-vf', (
            f"subtitles={formatted_sub}:force_style="
            f"'FontName=HelveticaRounded-Bold,FontSize={Config.FONT_SIZE},"
            f"PrimaryColour={Config.FONT_COLOR},Outline={Config.BORDER_WIDTH}',"
            f"drawtext=text='{Config.WATERMARK}':fontfile='{font_path}':"
            "x=w-tw-10:y=10:fontsize=24:fontcolor=white:"
            "borderw=2:bordercolor=black"
        ),
        '-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '20',
        '-tag:v', 'hvc1', '-c:a', 'copy', '-y', out_location
    ]

    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    error_output = await read_stderr(start, msg, process)
    await process.wait()

    if process.returncode == 0:
        await safe_edit_message(msg, f'✅ **Muxing Completed!**\n⏳ Time: {round(time.time() - start)}s')

        screenshots = await generate_screenshots(out_location)
        await send_screenshots(msg, screenshots)

        return output
    else:
        trimmed_error = error_output[-3000:] if len(error_output) > 3000 else error_output
        await safe_edit_message(msg, f'❌ **Muxing Failed!**\n\nError:\n```{trimmed_error}```')
        return False
