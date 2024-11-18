import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from Database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

db = Database.get_instance()

class TelegramBot:
    def __init__(self, token):
        self.application = ApplicationBuilder().token(token).build()
        self.add_handlers()

    def add_handlers(self):
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('add_shipment', self.add_shipment))
        self.application.add_handler(CommandHandler('track', self.track_shipment))
        self.application.add_handler(CommandHandler('status', self.update_status))
        self.application.add_handler(CommandHandler('providers', self.list_providers))
        self.application.add_handler(CommandHandler('add_provider', self.add_provider))
        self.application.add_handler(CommandHandler('ongoing_shipments', self.ongoing_shipment))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_command))


    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! I'm a shipment tracking bot.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text="""Available commands:
/start: Start the bot.
/help: Show this help message.
/add_shipment `code` `provider`: Add a new shipment (code and provider are required).
/ongoing_shipments: Return all shipment that are not dilivered.
/track `shipment_id`: Track a shipment by its ID.
/status `shipment_id` `status`: Update the status of a shipment (status can be False: Pending, True:Delivered).
/providers: List all available shipping providers.
/add_provider `name` `url`: Add a new shipping provider (name and url are required).""")

    async def ongoing_shipment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ongoing = db.get_all_ongoing_shipments()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"```\n{ongoing}\n```", parse_mode="Markdown")
        
                                       
    async def add_shipment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = update.message.text
            parts = message.split()
            if len(parts) < 3:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: `/add_shipment code provider`", parse_mode="Markdown")
            else:
                code = parts[1]
                provider = parts[2]
                shipment_id = db.insert_shipment(code, provider, False)
                db.add_to_current_tracking(shipment_id)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Shipment added with ID:\n```\n{shipment_id}\n```", parse_mode="Markdown")
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error adding shipment:\n```\n{e}\n```", parse_mode="Markdown")


    async def track_shipment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.split()
        if len(text) < 2:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /track `shipment_id`", parse_mode="Markdown")
            return
        try:
            input_text = update.message.text.split()[1]
            shipment = db.get_shipment(input_text)
            if shipment:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Shipment details:\nID: `{shipment[0]}`\nCode: `{shipment[1]}`\nProvider: `{shipment[2]}`\nStatus: `{shipment[3]}`", parse_mode="Markdown")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Shipment not found.")
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error adding shipment:\n```\n{e}\n```", parse_mode="Markdown")

    async def update_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = update.message.text.split()
            if len(message) < 2:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /status `shipment_id` [`status`]", parse_mode="Markdown")
                return

            shipment_id = message[1]

            if len(message) == 2:  # Only shipment ID provided, retrieve status
                shipment = db.get_shipment(shipment_id)
                if shipment:
                    await context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=f"Shipment status for ID {shipment_id}: {shipment[3]}")
                else:
                    await context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=f"Shipment with ID '{shipment_id}' not found.")
            else:  # Shipment ID and new status provided, update status
                status = message[2].lower() == "true"
                success = db.update_shipment_status(shipment_id, status)
                if success:
                    await context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=f"Shipment status updated successfully.")
                else:
                    await context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=f"Error updating shipment status.")
        except Exception as e:
            await context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=f"Error:\n```\n{e}\n```", parse_mode="Markdown")

    async def list_providers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            providers = db.get_all_providers()
            if providers:
                provider_list = "\n".join([f"{p[1]} ({p[2]})" for p in providers]) #Format the output nicely
                await context.bot.send_message(disable_web_page_preview=True, chat_id=update.effective_chat.id, text=f"Available providers:\n{provider_list}")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="No providers found.")
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error adding shipment:\n```\n{e}\n```", parse_mode="Markdown")

    async def add_provider(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            message = update.message.text.split()
            if len(message) < 3:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /add_provider `name` `url`", parse_mode="Markdown")
                return
            name = message[1]
            url = message[2]
            provider_id = db.add_ship_provider(name, url)
            if provider_id:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Provider '{name}' added successfully.")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error adding provider.")
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error adding shipment:\n```\n{e}\n```", parse_mode="Markdown")

    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")



    def run(self):
        self.application.run_polling()


if __name__ == '__main__':
    from dotenv import load_dotenv
    try:
        load_dotenv()
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN not found in .env file.")
        bot = TelegramBot(BOT_TOKEN)
        bot.run()
    except Exception as e:
        logging.error(f"An error occurred: {e}")