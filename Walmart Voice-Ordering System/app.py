import speech_recognition as sr
import spacy
import random
from gtts import gTTS
import os
from fuzzywuzzy import process
from word2number import w2n
import re
from flask import Flask, render_template, url_for,jsonify, request

from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Load the English language model for spaCy
nlp = spacy.load("en_core_web_sm")

# Example product list from Walmart dataset (simplified)
walmart_products = [
    'apple', 'banana', 'orange', 'milk', 'bread', 'eggs',
    'cheese', 'chicken', 'beef', 'pork', 'fish', 'shrimp',
    'lettuce', 'tomato', 'cucumber', 'carrot', 'broccoli',
    'onion', 'garlic', 'potato', 'rice', 'pasta', 'flour',
    'sugar', 'salt', 'pepper', 'oil', 'butter', 'yogurt',
    'cereal', 'coffee', 'tea', 'juice', 'soda', 'water',
    'chocolate', 'candy', 'ice cream', 'cookie', 'cake',
    'wine', 'beer', 'whiskey', 'vodka', 'rum', 'toothpaste',
    'soap', 'shampoo', 'conditioner', 'laundry detergent',
    'dish soap', 'paper towels', 'toilet paper', 'trash bags'
]

@app.route('/')
def index():
    return render_template('index.html')

# Ensure this directory exists within your Flask application structure
audio_dir = os.path.join(app.static_folder, 'audio')
if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Assuming you're saving the file temporarily for processing
        temp_path = os.path.join('/tmp', audio_file.filename)
        audio_file.save(temp_path)

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)
            # Process your audio_data here

        # Clean up temporary file
        os.remove(temp_path)
        return jsonify({'message': 'Audio processed successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 500

def order():
    order_text = request.form['orderText']
    order_components = {"items": []}
    parse_order_nlp(order_text, order_components)
    total_price = calculate_price(order_components)
    order_summary = construct_order_summary(order_components)
    return jsonify({"orderSummary": order_summary, "totalPrice": total_price})


def speak_message(message):
    """Converts the given message to speech and plays it."""
    tts = gTTS(text=message, lang='en')
    save_path = 'temp_message.mp3'  # Adjust the path as needed
    tts.save(save_path)
    os.system(f"mpg123 -q '{save_path}'")
    os.remove(save_path)  # Clean up after playing the message

def recognize_speech(recognizer, source):
    recognizer.adjust_for_ambient_noise(source)
    print("Please speak your order now...")
    audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio).lower()  # Convert to lowercase to match product list
    except sr.RequestError:
        return "API unavailable"
    except sr.UnknownValueError:
        return "Unable to recognize speech"

def parse_order_nlp(order, order_components):
    """Uses spaCy to parse the recognized speech for product names and quantities."""
    print(f"Parsing Order: {order}")  # Debug print
    doc = nlp(order)
    current_quantity = 1

    for token in doc:
        try:
            # Try to convert the token to a number
            current_quantity = w2n.word_to_num(token.text)
        except ValueError:
            # If the token is not a number, check for product names
            product_name = token.text.lower()
            plural_product_name = product_name + 's' if not product_name.endswith('s') else product_name[:-1]

            if product_name in walmart_products or plural_product_name in walmart_products:
                # Use the singular form of the product name for consistency
                product_name = product_name if product_name in walmart_products else plural_product_name
                # Check if the item is already in the order
                existing_item = next((item for item in order_components['items'] if item[1].lower() == product_name), None)
                if existing_item:
                    # Update the quantity of the existing item
                    order_components['items'].remove(existing_item)
                    order_components['items'].append((existing_item[0] + current_quantity, product_name.capitalize()))
                else:
                    # Add the new item to the order
                    order_components['items'].append((current_quantity, product_name.capitalize()))
                print(f"Added to Order: {current_quantity} x {product_name.capitalize()}")  # Debug print
                # Reset the quantity only after successfully adding an item
                current_quantity = 1

    print(f"Final Order Components: {order_components}")  # Debug print

def calculate_price(order_components):
    """Calculates the total price of the order."""
    total_price = 0.0
    for quantity, item_name in order_components['items']:
        base_price = random.uniform(1.0, 10.0)  # Simplified pricing logic
        total_price += base_price * quantity
    return total_price

def construct_order_summary(parsed_order):
    """Generates a summary of the order."""
    order_summary_parts = []
    for quantity, item in parsed_order['items']:
        item_summary = f"{quantity}  {item}"
        order_summary_parts.append(item_summary)
    return ', '.join(order_summary_parts)


@app.route('/voice_checkin', methods=['GET'])
def main_process():
    """Main process integrating speech recognition, NLP parsing, and order handling."""
    # Initialize the recognizer
    recognizer = sr.Recognizer()
    # Initialize the microphone input
    with sr.Microphone() as source:
        speak_message("Welcome to Walmart online ordering system!")
        order_components = {"items": []}
        adding_items = True  # Flag to control whether we are adding items to the order

        while adding_items:
            # Initial or additional order prompt
            if not order_components['items']:
                speak_message("What would you like to order today? Please speak your order now...")
            elif order_components['items']:
                speak_message("Would you like to add any other items to your order? Please say Yes to add more items or No to proceed to checkout.")
                add_more = recognize_speech(recognizer, source).strip().lower()
                if "no" in add_more:
                    break
                elif "yes" in add_more:
                    speak_message("Please speak your additional order now...")
                else:
                    speak_message("Sorry, I didn't understand. Please say Yes or No.")
                    continue
            
            spoken_order = recognize_speech(recognizer, source).strip().lower()

            if spoken_order not in ["api unavailable", "unable to recognize speech"]:
                parse_order_nlp(spoken_order, order_components)
            else:
                speak_message(spoken_order)

        # Calculate total price and construct order summary after all items have been added
        total_price = calculate_price(order_components)
        order_summary = construct_order_summary(order_components)
        speak_message(f"Here's your order summary and price: {order_summary}. Total Price: ${total_price:.2f}")
        speak_message("Thank you for Shopping at Walmart! Please pay through the payment gateway.")
        return jsonify({"checkInConfirmed": True, "orderComponents": {"orderSummary": order_summary, "totalPrice": total_price}, "message": "Your order has been confirmed"})

        
if __name__ == '__main__':
    app.run(debug=True)