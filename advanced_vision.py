import os
from rembg import remove
from PIL import Image
from transformers import pipeline

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
import cv2
import numpy as np
from sklearn.cluster import KMeans

def get_dominant_hex(image_path, k=3):
    """Extracts the most dominant color from the clothing item using KMeans clustering."""
    image = cv2.imread(image_path)
    if image is None: return "#000000"
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    pixels = image.reshape(-1, 3)
    # Ignore pure white background
    non_white_pixels = pixels[np.any(pixels < [240, 240, 240], axis=1)]
    if len(non_white_pixels) == 0: return "#ffffff"
        
    if len(non_white_pixels) > 5000:
        indices = np.random.choice(len(non_white_pixels), 5000, replace=False)
        non_white_pixels = non_white_pixels[indices]
        
    kmeans = KMeans(n_clusters=k, n_init=3)
    kmeans.fit(non_white_pixels)
    counts = np.bincount(kmeans.labels_)
    dominant_color = kmeans.cluster_centers_[np.argmax(counts)]
    return '#{:02x}{:02x}{:02x}'.format(int(dominant_color[0]), int(dominant_color[1]), int(dominant_color[2]))

def analyze_clothing_model(image_path):
    """Analyzes an image and returns clothing metadata with high-accuracy prompting."""
    clean_image = preprocess_image(image_path)
    if not clean_image: 
        raise Exception("Failed to preprocess image")

    # 1. Improved Labels (Making them sound like natural sentences for the AI)
    category_labels = ["a pair of jeans", "a pair of cargo pants", "a t-shirt", "a button-down shirt", "a jacket or coat"]
    color_labels = ["black", "navy blue", "white", "grey", "olive green", "sky blue", "crimson red", "yellow"]
    fit_labels = ["slim fit clothing", "regular straight fit clothing", "loose baggy clothing", "oversized clothing"]

    # 2. Improved Prompting (Guiding the AI on exactly what to look for)
    cat_res = classifier(clean_image, candidate_labels=category_labels, hypothesis_template="This is a photo of {}.")
    col_res = classifier(clean_image, candidate_labels=color_labels, hypothesis_template="The primary color of this clothing item is {}.")
    fit_res = classifier(clean_image, candidate_labels=fit_labels, hypothesis_template="The fit or silhouette of this clothing item is extremely {}.")

    raw_category = cat_res[0]['label']
    raw_color = col_res[0]['label']
    raw_fit = fit_res[0]['label']
    
    # Map back to our simple database rules
    db_fit = "Regular"
    if "slim" in raw_fit: db_fit = "Slim"
    elif "baggy" in raw_fit: db_fit = "Baggy"
    elif "oversized" in raw_fit: db_fit = "Oversized"

    # Clean up the category name for the database
    db_cat = raw_category.replace("a pair of ", "").replace("a ", "")

    temperature = determine_temperature(raw_color)
    main_category = "Bottom" if "pants" in db_cat or "jeans" in db_cat else "Top"
    
    # 3. OpenCV Advanced Color Extraction
    hex_code = get_dominant_hex("clean_subject.png")

    return {
        "category": main_category,
        "sub_category": db_cat,
        "color": raw_color,
        "hex_code": hex_code,
        "temperature": temperature,
        "fit": db_fit
    }