import requests

class TelegramBot:
    def __init__(self, bot_token, chat_id):
        """Initializes the TelegramBot with the bot token and chat ID."""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message):
        """Sends a message to the specified chat ID using Markdown formatting."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print("Message sent successfully!")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")
            return None

    def send_photo(self, photo_path):
        """Sends a photo to the specified chat ID."""
        url = f"{self.base_url}/sendPhoto"
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                response = requests.post(url, data={'chat_id': self.chat_id}, files=files)
                response.raise_for_status()
                print("Photo sent successfully!")
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending photo: {e}")
            return None

    def send_document(self, document_path, caption=None):
        """Sends a document (file) to the specified chat ID."""
        url = f"{self.base_url}/sendDocument"
        try:
            with open(document_path, 'rb') as document:
                files = {'document': document}
                data = {'chat_id': self.chat_id}
                if caption:
                    data['caption'] = caption
                response = requests.post(url, data=data, files=files)
                response.raise_for_status()
                print("Document sent successfully!")
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending document: {e}")
            return None
        
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not bot_token or not chat_id:
        print("Error: BOT_TOKEN or CHAT_ID not found in .env file.")
        exit(1)

    bot = TelegramBot(bot_token, chat_id)

    message = "*This is a test message in Markdown!*  [Link to Google](https://www.google.com)"
    response = bot.send_message(message)
    if response:
        print(response)

    #photo_response = bot.send_photo('path/to/photo.jpg')
    #if photo_response:
    #    print(photo_response)


    #document_response = bot.send_document('path/to/document.pdf', caption="Here's a document!")
    #if document_response:
    #    print(document_response)