
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot API Key
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    welcome_message = (
        "Welcome to the PNG Downloader Bot! 👋\n\n"
        "I can help you download high-quality PNG images from cleanpng.com.\n\n"
        "**How to use me:**\n"
        "1. Find a PNG image on cleanpng.com.\n"
        "2. Send me the link to the image page (e.g., https://www.cleanpng.com/png-red-bow-decoration-8187405/).\n"
        "3. I'll download the PNG and send it back to you!\n\n"
        "Let's get started! Send me a link to a PNG you want to download."
    )
    await update.message.reply_text(welcome_message)

async def download_png(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download the PNG from a cleanpng.com URL using Selenium."""
    url = update.message.text
    if "cleanpng.com" not in url:
        await update.message.reply_text("Please send a valid URL from cleanpng.com.")
        return

    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set up webdriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)
        time.sleep(5)  # Wait for the page to load

        # Find the download link
        download_link = driver.find_element(By.LINK_TEXT, "Free Download")
        png_url = download_link.get_attribute('href')

        driver.quit()

        if not png_url:
            await update.message.reply_text("Could not find the download link on the page. Please make sure the URL is correct.")
            return

        # Download the PNG
        png_response = requests.get(png_url)
        png_response.raise_for_status()

        # Check if the downloaded file is a PNG
        if "image/png" not in png_response.headers.get("Content-Type", ""):
            await update.message.reply_text("The downloaded file is not a PNG. Please try a different URL.")
            return

        # Save the PNG
        file_name = url.split("/")[-2] + ".png"
        with open(file_name, "wb") as f:
            f.write(png_response.content)

        # Send the PNG to the user
        await update.message.reply_document(document=open(file_name, "rb"))

        # Clean up the file
        os.remove(file_name)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await update.message.reply_text("An unexpected error occurred. Please try again later.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_png))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
