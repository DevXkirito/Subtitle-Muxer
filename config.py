import os

class Config:
    # Font Configuration
    FONT_NAME = "HelveticaRounded-Bold"
    FONT_SIZE = 18
    FONT_COLOR = "&H00FFFFFF"     # ARGB: White
    BORDER_COLOR = "&H00000000"   # ARGB: Black
    BORDER_WIDTH = 1.5
    WATERMARK = "CHS ANIME"

    # Bot Configuration
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")

    APP_ID = int(os.environ.get('APP_ID', 0))
    API_HASH = os.environ.get('API_HASH', '')

    # Allowed Users (converted to list of integers)
    ALLOWED_USERS = [int(x.strip()) for x in os.environ.get('ALLOWED_USERS', '1098504493').split(',')]

    # Download Directory
    DOWNLOAD_DIR = 'downloads'
