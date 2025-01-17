# Install transformers from source - only needed for versions <= v4.34
# pip install git+https://github.com/huggingface/transformers.git
# pip install accelerate

import logging
import torch
from transformers import pipeline
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging to monitor bot activity
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Adjust logging level for httpx to suppress verbose logs
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Load the TinyLlama model and set it up for text generation
pipe = pipeline(
    "text-generation",
    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# Define command and message handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command by greeting the user."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hello, {user.mention_html()}! :)",
        reply_markup=ForceReply(selective=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command by providing a help message."""
    await update.message.reply_text("Help!" )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process the user's message using TinyLlama and send back a generated response.
    """
    # Get the message sent by the user
    user_message = update.message.text

    messages = [
        {"role": "system", 
         "content": "You are a friendly chatbot who always responds in the style of a pirate."
        },
        {"role": "user", "content": user_message},
    ]
    # Apply the chat template to prepare the input prompt for the model
    prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # Generate the response using TinyLlama model
    outputs = pipe(
            prompt,
            max_new_tokens=256,  # maximum length of the generated text
            do_sample=True,      # Enable sampling for diverse responses
            temperature=0.7,     # temperature to control randomness
            top_k=50,            # top-k sampling to limit the vocabulary size
            top_p=0.95           # nucleus sampling to focus on the top probable tokens
        )
    # Extract the assistant's response from the generated output
    response = outputs[0]["generated_text"].split("</s>")[-1].strip()

    


    # Send the generated response back to the user on Telegram
    await update.message.reply_text(response)


def main() -> None:
    """Set up and run the Telegram bot."""
    # Create the Application instance and set the bot's token
    application = Application.builder().token("7940279625:AAFLwqQXaKXKU5HxLFHY5xQl6DJCfH4MfwI").build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Register a handler for user messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot until interrupted
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
