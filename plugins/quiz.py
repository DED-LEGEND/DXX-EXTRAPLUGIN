import random
import requests
import time
import asyncio

from pyrogram import filters
from pyrogram.enums import PollType, ChatAction
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from ERAVIBES import app

# Module metadata
__MODULE__ = "Qᴜɪᴢ"
__HELP__ = """
/quiz - Sᴛᴀʀᴛ ǫᴜɪᴢ ᴍᴏᴅᴇ. Sᴇʟᴇᴄᴛ ᴛʜᴇ ɪɴᴛᴇʀᴠᴀʟ ғᴏʀ ǫᴜɪᴢᴢᴇs ᴛᴏ ʙᴇ sᴇɴᴛ. 

• **Intervals:**
   - 30 seconds
   - 1 minute
   - 5 minutes
   - 10 minutes
• **Stop**: Pʀᴇss ᴛʜᴇ "Sᴛᴏᴘ Qᴜɪᴢ" ʙᴜᴛᴛᴏɴ ᴛᴏ sᴛᴏᴘ ǫᴜɪᴢ ʟᴏᴏᴘ.
"""

# Dictionary to track user quiz loops and their intervals
quiz_loops = {}

# Function to fetch a quiz question from the API
async def fetch_quiz_question():
    categories = [9, 17, 18, 20, 21, 27]  # Quiz categories
    url = f"https://opentdb.com/api.php?amount=1&category={random.choice(categories)}&type=multiple"
    response = requests.get(url).json()

    question_data = response["results"][0]
    question = question_data["question"]
    correct_answer = question_data["correct_answer"]
    incorrect_answers = question_data["incorrect_answers"]

    all_answers = incorrect_answers + [correct_answer]
    random.shuffle(all_answers)

    cid = all_answers.index(correct_answer)

    return question, all_answers, cid

# Function to send a quiz poll
async def send_quiz_poll(client, message):
    question, all_answers, cid = await fetch_quiz_question()

    await app.send_poll(
        chat_id=message.chat.id,
        question=question,
        options=all_answers,
        is_anonymous=False,
        type=PollType.QUIZ,
        correct_option_id=cid,
    )

# /quiz command to show time interval options
@app.on_message(filters.command(["quiz"]))
async def quiz(client, message):
    user_id = message.from_user.id

    # Creating time interval buttons and stop button arranged in 4x2 grid
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("30s", callback_data="30_sec"), InlineKeyboardButton("1min", callback_data="1_min")],
            [InlineKeyboardButton("5min", callback_data="5_min"), InlineKeyboardButton("10min", callback_data="10_min")],
            [InlineKeyboardButton("Stop Quiz", callback_data="stop_quiz")],
        ]
    )

    # Sending the buttons with a description
    await message.reply_text(
        "**Choose how often you want the quiz to run:**\n\n"
        "- 30s: Quiz every 30 seconds\n"
        "- 1min: Quiz every 1 minute\n"
        "- 5min: Quiz every 5 minutes\n"
        "- 10min: Quiz every 10 minutes\n\n"
        "**Press 'Stop Quiz' to stop the quiz loop at any time.**",
        reply_markup=keyboard
    )

# Handling button presses for time intervals
@app.on_callback_query(filters.regex(r"^\d+_sec$|^\d+_min$"))
async def start_quiz_loop(client, callback_query):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    if user_id in quiz_loops:
        await callback_query.answer("Quiz loop is already running!", show_alert=True)
        return

    # Determine the interval based on the button pressed
    if callback_query.data == "30_sec":
        interval = 30
        interval_text = "30 seconds"
    elif callback_query.data == "1_min":
        interval = 60
        interval_text = "1 minute"
    elif callback_query.data == "5_min":
        interval = 300
        interval_text = "5 minutes"
    elif callback_query.data == "10_min":
        interval = 600
        interval_text = "10 minutes"

    # Delete the original message with buttons
    await callback_query.message.delete()

    # Confirm that the quiz loop has started
    await callback_query.message.reply_text(f"✅ Quiz loop started! You'll receive a quiz every {interval_text}.")

    quiz_loops[user_id] = True  # Mark loop as running

    # Start the quiz loop with the selected interval
    while quiz_loops.get(user_id, False):
        await send_quiz_poll(client, callback_query.message)
        await asyncio.sleep(interval)  # Wait for the selected time interval

# Handling the stop button press
@app.on_callback_query(filters.regex("stop_quiz"))
async def stop_quiz_loop(client, callback_query):
    user_id = callback_query.from_user.id

    if user_id not in quiz_loops:
        await callback_query.answer("No quiz loop is running!", show_alert=True)
    else:
        quiz_loops.pop(user_id)  # Stop the loop
        await callback_query.message.delete()  # Remove the old message
        await callback_query.message.reply_text("⛔ Quiz loop stopped!")
