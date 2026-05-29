import os
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv
from rembg import remove
from PIL import Image
from transformers import pipeline

# Load the hidden password
load_dotenv()

print("Loading AI Models... (This takes a few seconds)")
classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")

def preprocess_image(input_path, output_path="clean_subject.png"):
    """Removes background and adds a solid white backdrop."""
    try:
        with open(input_path, 'rb') as i:
            input_data = i.read()
        output_data = remove(input_data)
        
        with open(output_path, 'wb') as o:
            o.write(output_data)
            
        clean_img = Image.open(output_path)
        if clean_img.mode == 'RGBA':
            white_bg = Image.new("RGB", clean_img.size, (255, 255, 255))
            white_bg.paste(clean_img, mask=clean_img.split()[3])
            return white_bg
        return clean_img
    except FileNotFoundError:
        print(f"Error: Could not find {input_path}.")
        return None

def determine_temperature(color_string):
    """Maps colors to warm, cool, or neutral for the styling engine."""
    warm_colors = ["crimson red", "mustard yellow", "bright yellow", "burnt orange", "burgundy maroon", "pastel pink", "dark brown"]
    cool_colors = ["navy blue", "sky blue", "royal blue", "olive green", "mint green", "purple"]
    
    if color_string in warm_colors:
        return "Warm"
    elif color_string in cool_colors:
        return "Cool"
    return "Neutral" # For blacks, whites, greys, and beiges

def save_to_database(user_id, category, sub_category, color, fit):
    """Opens a connection to PostgreSQL and saves the AI's findings."""
    try:
        connection = psycopg2.connect(
            user="postgres", 
            password=os.getenv("DB_PASSWORD"), 
            host="127.0.0.1",
            port="5432",
            database="ai_stylist"
        )
        cursor = connection.cursor()

        # Execute the INSERT statement
        insert_query = """
            INSERT INTO Garments (user_id, category, sub_category, primary_color, color_temperature, fit)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Calculate temperature
        temp = determine_temperature(color)
        
        # We assume tops/jackets are 'Top' and pants/jeans are 'Bottom' based on the word
        main_category = "Bottom" if "pants" in sub_category or "jeans" in sub_category else "Top"
        
        # Pass the variables safely to prevent SQL injection
        cursor.execute(insert_query, (user_id, main_category, sub_category, color, temp, fit))
        connection.commit()
        
        print("\n✅ SUCCESS: Garment automatically saved to the PostgreSQL database!")

    except Error as e:
        print(f"\n❌ Database Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def analyze_clothing(image_path, user_id=1):
    clean_image = preprocess_image(image_path)
    if not clean_image: return

    # The AI's Descriptive Menu
    category_labels = ["t-shirt", "casual button-down shirt", "jeans", "cargo pants", "jacket"]
    color_labels = ["white", "black", "navy blue", "sky blue", "olive green", "crimson red", "yellow", "grey"]
    fit_labels = ["tight slim fit", "regular straight fit", "loose baggy fit", "oversized dropped-shoulder fit"]

    print("\n--- AI is scanning the clothing... ---")
    
    # Run the AI
    cat_res = classifier(clean_image, candidate_labels=category_labels)
    col_res = classifier(clean_image, candidate_labels=color_labels)
    fit_res = classifier(clean_image, candidate_labels=fit_labels)

    # 1. Extract the raw text of the top prediction
    raw_category = cat_res[0]['label']
    raw_color = col_res[0]['label']
    raw_fit = fit_res[0]['label']
    
    # 2. Map the descriptive fit back to the strict database rules
    db_fit = "Regular"
    if "slim" in raw_fit: db_fit = "Slim"
    elif "baggy" in raw_fit: db_fit = "Baggy"
    elif "oversized" in raw_fit: db_fit = "Oversized"

    print(f"Detected: {raw_color} {raw_category} ({db_fit} fit)")

    # 3. Save it directly to the database!
    save_to_database(user_id, raw_category, raw_category, raw_color, db_fit)

if __name__ == "__main__":
    # Test it with a photo!
    analyze_clothing("test_shirt.jpg", user_id=1)