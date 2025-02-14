from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
import pysubs2

# Track user states
user_states = {}

# Command: /convert - Show format options
@Client.on_message(filters.command("convert") & filters.private)
async def start_conversion(client, message):
    user_id = message.from_user.id
    user_states[user_id] = {"waiting_for_format": True}  # Mark user as selecting format

    buttons = [
        [InlineKeyboardButton("SRT ➝ ASS", callback_data="format_srt_ass")],
        [InlineKeyboardButton("ASS ➝ SRT", callback_data="format_ass_srt")],
        [InlineKeyboardButton("TXT ➝ ASS", callback_data="format_txt_ass")],
    ]

    await message.reply_text(
        "Select the subtitle format you want to convert:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
# Handle format selection
@Client.on_callback_query(filters.regex("^format_"))
async def handle_format_selection(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    conversion_type = callback_query.data.replace("format_", "")

    user_states[user_id] = {
        "waiting_for_file": True,
        "conversion_type": conversion_type
    }

    await callback_query.message.edit_text(
        f"Now, please send me the subtitle file you want to convert to `{conversion_type.upper()}` format."
    )

# Handle subtitle file upload
@Client.on_message(filters.document)
async def handle_subtitle(client, message):
    user_id = message.from_user.id
    user_data = user_states.get(user_id)

    if not user_data or "waiting_for_file" not in user_data:
        await message.reply_text("❌ Please use /convert first and select a format before sending a file.")
        return

    # Download file
    file_path = await message.download()
    conversion_type = user_data["conversion_type"]

    # Check file extension before conversion
    file_extension = os.path.splitext(file_path)[-1].lower()
    if conversion_type == "srt_ass" and file_extension != ".srt":
        await message.reply_text("❌ Please send a `.srt` file.")
        return
    elif conversion_type == "ass_srt" and file_extension != ".ass":
        await message.reply_text("❌ Please send an `.ass` file.")
        return
    elif conversion_type == "txt_ass" and file_extension != ".txt":
        await message.reply_text("❌ Please send a `.txt` file.")
        return

    # Perform conversion
    converted_file = None
    if conversion_type == "srt_ass":
        converted_file = convert_srt_to_ass(file_path)
    elif conversion_type == "ass_srt":
        converted_file = convert_ass_to_srt(file_path)
    elif conversion_type == "txt_ass":
        converted_file = convert_txt_to_ass(file_path)

    # Send converted file if successful
    if converted_file:
        await message.reply_document(converted_file, caption="✅ Here is your converted subtitle file.")
        os.remove(converted_file)  # Cleanup after sending

    os.remove(file_path)  # Remove original file
    user_states.pop(user_id, None)  # Reset user state
