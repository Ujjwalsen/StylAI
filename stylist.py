import psycopg2
from psycopg2 import Error

def connect_to_db():
    """Establishes a connection to the local PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            user="postgres", # Default pgAdmin username
            password= DB_PASSWORD, # Replace with your password
            host="127.0.0.1",
            port="5432",
            database="ai_stylist"
        )
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def get_user_profile(cursor, user_id):
    """Fetches the user's styling parameters."""
    cursor.execute("SELECT skin_undertone, style_preference FROM Users WHERE user_id = %s", (user_id,))
    return cursor.fetchone()

def get_wardrobe(cursor, user_id):
    """Fetches all available garments for the user."""
    cursor.execute("""
        SELECT garment_id, category, primary_color, color_temperature, fit 
        FROM Garments 
        WHERE user_id = %s
    """, (user_id,))
    return cursor.fetchall()

def generate_outfit(user_id):
    """The core logic engine that matches clothes based on rules."""
    conn = connect_to_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # 1. Get Data
        user_profile = get_user_profile(cursor, user_id)
        wardrobe = get_wardrobe(cursor, user_id)
        
        if not user_profile or not wardrobe:
            print("Not enough data to style this user.")
            return

        undertone, style_pref = user_profile
        print(f"Styling for User {user_id} | Undertone: {undertone} | Style: {style_pref}\n")

        # 2. Separate Wardrobe by Category
        tops = [item for item in wardrobe if item[1] == 'Top']
        bottoms = [item for item in wardrobe if item[1] == 'Bottom']

        # 3. Apply Styling Rules (The "AI" part of the MVP)
        best_outfit = None
        highest_score = 0

        for top in tops:
            for bottom in bottoms:
                score = 5 # Base score
                
                top_id, top_cat, top_color, top_temp, top_fit = top
                bot_id, bot_cat, bot_color, bot_temp, bot_fit = bottom

                # Rule A: Color Theory Match
                # If the garment temperature matches the user's undertone, boost score
                if top_temp == undertone:
                    score += 2
                if bot_temp == undertone:
                    score += 2

                # Rule B: Silhouette Balance (Basic)
                # Avoid pairing oversized tops with baggy bottoms unless the style is Streetwear
                if top_fit == 'Oversized' and bot_fit == 'Baggy':
                    if style_pref == 'Streetwear':
                        score += 3 # Highly desired for this style
                    else:
                        score -= 2 # Looks sloppy for other styles

                # Track the best combination
                if score > highest_score:
                    highest_score = score
                    best_outfit = (top, bottom)

        # 4. Output the Result
        if best_outfit:
            print(f"--- 🌟 SUGGESTED OUTFIT (Score: {highest_score}/10) 🌟 ---")
            print(f"TOP: {best_outfit[0][4]} {best_outfit[0][2]} {best_outfit[0][1]} (ID: {best_outfit[0][0]})")
            print(f"BOTTOM: {best_outfit[1][4]} {best_outfit[1][2]} {best_outfit[1][1]} (ID: {best_outfit[1][0]})")
        else:
            print("Could not find a suitable outfit combination.")

    finally:
        if conn:
            cursor.close()
            conn.close()

# Run the engine for our dummy user (User ID 1)
if __name__ == "__main__":
    generate_outfit(1)