from rembg import remove
from PIL import Image
from transformers import pipeline
import io

print("Loading AI Models... (Preprocessing and Classification)")
# Load the Hugging Face classifier
classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")

def preprocess_image(input_path, output_path="clean_subject.png"):
    """Removes the background from the image and saves a clean transparent PNG."""
    try:
        with open(input_path, 'rb') as i:
            input_data = i.read()
            
        print(f"Removing background from {input_path}...")
        output_data = remove(input_data)
        
        with open(output_path, 'wb') as o:
            o.write(output_data)
            
        print(f"Clean image saved as {output_path}")
        return Image.open(output_path)
    
    except FileNotFoundError:
        print(f"Error: Could not find {input_path}.")
        return None

def analyze_clothing(image_path):
    # 1. Preprocess: Strip the background first!
    clean_image = preprocess_image(image_path)
    
    if not clean_image:
        return

    # 2. Define the exact traits (Now we can use simpler labels!)
    category_labels = ["t-shirt", "button-down shirt", "jeans", "cargo pants", "jacket"]
    color_labels = ["navy blue", "light blue", "white", "black", "olive green", 
        "crimson red", "yellow", "mustard yellow", "pink", "grey",
        "brown", "orange", "purple", "maroon"]
    fit_labels = ["slim fit", "baggy fit", "oversized fit"]

    print("\n--- Analyzing Cleaned Image ---")
    
    # 3. Interrogate the clean image
    category_results = classifier(clean_image, candidate_labels=category_labels)
    color_results = classifier(clean_image, candidate_labels=color_labels)
    fit_results = classifier(clean_image, candidate_labels=fit_labels)

    # 4. Print the highest probability match
    print("\n🏷️ CATEGORY:")
    print(f"{category_results[0]['label']} (Confidence: {category_results[0]['score']:.2f})")
    
    print("\n🎨 COLOR:")
    print(f"{color_results[0]['label']} (Confidence: {color_results[0]['score']:.2f})")

    print("\n📏 FIT:")
    print(f"{fit_results[0]['label']} (Confidence: {fit_results[0]['score']:.2f})")

if __name__ == "__main__":
    # Point this at the photo of the guy in the white shirt!
    analyze_clothing("test_shirt.jpg")