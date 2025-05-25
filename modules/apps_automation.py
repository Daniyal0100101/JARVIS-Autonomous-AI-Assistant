def send_whatsapp_message(recipient, message):
    """
    Sends a WhatsApp message using pywhatkit, handling the import dynamically.
    
    :param recipient: The phone number to send the message to (string format with country code).
    :param message: The content of the message to send.
    :return: Success or error message as a string.
    """
    try:
        import pywhatkit as kit
        # Send the message instantly
        kit.sendwhatmsg_instantly(recipient, message, wait_time=10, tab_close=True)
        return "The message was sent successfully!"
    except ImportError:
        return "Failed to import pywhatkit, please ensure it is installed."
    except Exception as e:
        return f"Failed to send the message: {e}"

# Example usage:
# if __name__ == "__main__":
#     recipient_number = "+923124681701"  # Replace with actual phone number
#     message_content = f"The 71 - 32 is: {71 - 32}"
#     result = send_whatsapp_message(recipient_number, message_content)
#     print(result)
