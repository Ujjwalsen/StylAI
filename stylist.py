def match_outfit(user_profile, wardrobe):
    """
    The core logic engine that matches clothes based on rules.
    Accepts:
        user_profile (dict): The user's settings (skin_undertone, style_preference, etc)
        wardrobe (list of dicts): The list of garments from Supabase DB.
    """
    
    undertone = user_profile.get("skin_undertone", "Neutral")
    style_pref = user_profile.get("style_preference", "Casual")
    
    # Sort garments by category
    tops = [item for item in wardrobe if item.get('category') == 'Top']
    bottoms = [item for item in wardrobe if item.get('category') == 'Bottom']

    outfits = []

    for top in tops:
        for bottom in bottoms:
            score = 5 # Base starting score
            
            top_temp = top.get('color_temperature')
            bot_temp = bottom.get('color_temperature')
            top_fit = top.get('fit')
            bot_fit = bottom.get('fit')

            # Rule A: Color Theory Match
            if top_temp == undertone:
                score += 2
            if bot_temp == undertone:
                score += 2

            # Rule B: Silhouette Balance
            if top_fit == 'Oversized' and bot_fit == 'Baggy':
                if style_pref == 'Streetwear':
                    score += 3
                else:
                    score -= 2 

            outfits.append({
                "top": top,
                "bottom": bottom,
                "score": score
            })

    if not outfits:
        return None

    # Sort the outfits from highest score to lowest
    outfits.sort(key=lambda x: x['score'], reverse=True)
    
    import random
    # Grab the top 3 highest scoring outfits (or fewer if there aren't 3)
    top_contenders = outfits[:3]
    
    # Return a random choice from those top outfits to maintain variety!
    return random.choice(top_contenders)