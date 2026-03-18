import os
from flask import Flask, request
import telebot
from openai import OpenAI

# 1. Setup Environment Variables
# These must be set in your Render Dashboard under 'Environment'
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
# Render provides the URL of your app in this variable automatically
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') 

# 2. Initialize Clients
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Configure OpenAI client for Hugging Face Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 3. Bot Handlers
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am your AI assistant powered by DeepSeek-R1. Send me a message to start chatting.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Send a "typing" action to improve user experience
        bot.send_chat_action(message.chat.id, 'typing')

        # Call the Hugging Face Router API (OpenAI Compatible)
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                },
            ],
        )

        # Extract response text
        response_text = chat_completion.choices[0].message.content
        bot.reply_to(message, response_text)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I encountered an error processing your request.")

# 4. Flask Webhook Logic
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    # Automatically set the webhook when the home page is visited
    # or when Render starts the service
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
        return "Webhook successfully set!", 200
    return "Render URL not found. Please set RENDER_EXTERNAL_URL.", 400

# 5. Execution
if __name__ == "__main__":
    # Render requires the app to listen on a specific port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
