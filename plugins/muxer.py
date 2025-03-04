from pyrogram import Client, filters
from helper_func.progress_bar import progress_bar
from helper_func.dbhelper import Database as Db
from helper_func.mux import softmux_vid, hardmux_vid
from config import Config
import time
import os

db = Db()

async def _check_user(filt, c, m):
    chat_id = str(m.from_user.id)
    return chat_id in Config.ALLOWED_USERS

check_user = filters.create(_check_user)

@Client.on_message(filters.command('softmux') & check_user & filters.private)
async def softmux(client, message):
    chat_id = message.from_user.id
    og_vid_filename = db.get_vid_filename(chat_id)
    og_sub_filename = db.get_sub_filename(chat_id)

    # Validation Checks
    text = ''
    if not og_vid_filename or not os.path.exists(os.path.join(Config.DOWNLOAD_DIR, og_vid_filename)):
        text += 'First send a Video File\n'
    if not og_sub_filename or not os.path.exists(os.path.join(Config.DOWNLOAD_DIR, og_sub_filename)):
        text += 'Send a Subtitle File!'
    
    if text:
        await client.send_message(chat_id, text)
        return

    sent_msg = await client.send_message(chat_id, 'Your File is Being Soft Subbed. This should be done in a few seconds!')

    softmux_filename = await softmux_vid(og_vid_filename, og_sub_filename, sent_msg)
    if not softmux_filename:
        return

    final_filename = db.get_filename(chat_id)
    os.rename(os.path.join(Config.DOWNLOAD_DIR, softmux_filename), os.path.join(Config.DOWNLOAD_DIR, final_filename))

    start_time = time.time()
    try:
        await client.send_document(
            chat_id,
            progress=progress_bar,
            progress_args=('Uploading your File!', sent_msg, start_time),
            document=os.path.join(Config.DOWNLOAD_DIR, final_filename),
            caption=final_filename
        )
        await sent_msg.edit(f'File Successfully Uploaded!\nTotal Time taken: {round(time.time() - start_time)} seconds')
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occurred while uploading the file!\nCheck logs for details.')

    # Safe Cleanup
    path = Config.DOWNLOAD_DIR + '/'
    if og_sub_filename and os.path.exists(path + og_sub_filename):
        os.remove(path + og_sub_filename)
    if og_vid_filename and os.path.exists(path + og_vid_filename):
        os.remove(path + og_vid_filename)
    if final_filename and os.path.exists(path + final_filename):
        os.remove(path + final_filename)

    db.erase(chat_id)


@Client.on_message(filters.command('hardmux') & check_user & filters.private)
async def hardmux(client, message):
    chat_id = message.from_user.id
    og_vid_filename = db.get_vid_filename(chat_id)
    og_sub_filename = db.get_sub_filename(chat_id)

    # Validation Checks
    text = ''
    if not og_vid_filename or not os.path.exists(os.path.join(Config.DOWNLOAD_DIR, og_vid_filename)):
        text += 'First send a Video File\n'
    if not og_sub_filename or not os.path.exists(os.path.join(Config.DOWNLOAD_DIR, og_sub_filename)):
        text += 'Send a Subtitle File!'
    
    if text:
        await client.send_message(chat_id, text)
        return

    sent_msg = await client.send_message(chat_id, 'Your File is Being Hard Subbed. This might take a long time!')

    hardmux_filename = await hardmux_vid(og_vid_filename, og_sub_filename, sent_msg)
    if not hardmux_filename:
        return
    
    final_filename = db.get_filename(chat_id)
    os.rename(os.path.join(Config.DOWNLOAD_DIR, hardmux_filename), os.path.join(Config.DOWNLOAD_DIR, final_filename))

    start_time = time.time()
    try:
        await client.send_document(  # 🔥 Changed from send_video to send_document
            chat_id,
            progress=progress_bar,
            progress_args=('Uploading your File!', sent_msg, start_time),
            document=os.path.join(Config.DOWNLOAD_DIR, final_filename),
            caption=final_filename
        )
        await sent_msg.edit(f'File Successfully Uploaded!\nTotal Time taken: {round(time.time() - start_time)} seconds')
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occurred while uploading the file!\nCheck logs for details.')

    # Safe Cleanup
    path = Config.DOWNLOAD_DIR + '/'
    if og_sub_filename and os.path.exists(path + og_sub_filename):
        os.remove(path + og_sub_filename)
    if og_vid_filename and os.path.exists(path + og_vid_filename):
        os.remove(path + og_vid_filename)
    if final_filename and os.path.exists(path + final_filename):
        os.remove(path + final_filename)

    db.erase(chat_id)
