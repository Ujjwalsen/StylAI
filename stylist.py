import os
import json
import requests
import google.generativeai as genai

def get_weather(city="New York"):
    """Fetches real-time weather from OpenWeatherMap"""
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key: return "70°F, Clear"
    
    try:
        res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial")
        data = res.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"{temp}°F, {desc}"
    except Exception as e:
        print("Weather API error:", e)
        return "70°F, Clear"

def match_outfit(user_profile, wardrobe, occasion="Casual", city="New York"):
    """
    Uses Gemini LLM to generate the absolute best outfit from the wardrobe.
    """
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    weather = get_weather(city)
    
    # Filter out items that are missing essential data
    clean_wardrobe = [
        {"garment_id": w['garment_id'], "category": w['category'], "sub_category": w['sub_category'], "color": w['primary_color'], "fit": w['fit']} 
        for w in wardrobe
    ]

    prompt = f"""
    You are an expert high-fashion celebrity stylist.
    Your client has the following profile:
    - Undertone: {user_profile.get('skin_undertone', 'Neutral')}
    - Style Preference: {user_profile.get('style_preference', 'Casual')}
    
    They are dressing for this occasion: {occasion}
    The current weather in their city is: {weather}
    
    Here is their digital wardrobe (JSON):
    {json.dumps(clean_wardrobe, indent=2)}
    
    Rules:
    1. You must pick exactly one 'Top' and exactly one 'Bottom' from the wardrobe.
    2. The outfit must be functionally appropriate for the weather.
    3. The outfit must match the occasion.
    4. Provide a creative, natural language reason (2-3 sentences) explaining why this outfit works perfectly for them today.
    
    Return ONLY a raw JSON object (without markdown code blocks) in this exact format:
    {{
       "top_id": <garment_id of chosen top>,
       "bottom_id": <garment_id of chosen bottom>,
       "reason": "<your explanation here>"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(text)
        
        top = next(item for item in wardrobe if item['garment_id'] == result['top_id'])
        bottom = next(item for item in wardrobe if item['garment_id'] == result['bottom_id'])
        
        return {
            "top": top,
            "bottom": bottom,
            "reason": result['reason'],
            "weather": weather
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None