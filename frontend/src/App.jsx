import React, { useState, useEffect } from 'react';
import './index.css';
import Auth from './Auth';

function App() {
  const [sessionUserId, setSessionUserId] = useState(null);
  const [wardrobe, setWardrobe] = useState([]);
  const [outfit, setOutfit] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [occasion, setOccasion] = useState("Casual");
  const [city, setCity] = useState("New York");
  const [tryOnImage, setTryOnImage] = useState(null);
  const [tryOnLoading, setTryOnLoading] = useState(false);
  
  const USER_ID = sessionUserId;

  useEffect(() => {
    if (sessionUserId) fetchWardrobe();
  }, [sessionUserId]);

  const fetchWardrobe = async () => {
    try {
      const res = await fetch(`http://localhost:8000/wardrobe/${USER_ID}`);
      const data = await res.json();
      if(Array.isArray(data)) setWardrobe(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (garment_id) => {
    if (!window.confirm("Remove this item from your wardrobe?")) return;
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/garments/${garment_id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        fetchWardrobe();
        if (outfit && (outfit.top.garment_id === garment_id || outfit.bottom.garment_id === garment_id)) {
            setOutfit(null); // Clear outfit if the deleted item was part of it
        }
      }
    } catch (e) {
      console.error(e);
      setError("Failed to delete garment.");
    }
    setLoading(false);
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", USER_ID);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        fetchWardrobe();
      } else {
          const errData = await res.json();
          setError(errData.detail || "Failed to upload image");
      }
    } catch (err) {
      console.error(err);
      setError("Network error communicating with the AI.");
    }
    setLoading(false);
  };

  const generateOutfit = async () => {
    setLoading(true);
    setError(null);
    setOutfit(null);
    setTryOnImage(null);
    try {
      const res = await fetch(`http://localhost:8000/style/${USER_ID}?occasion=${occasion}&city=${city}`);
      const data = await res.json();
      if (data.outfit) {
        setOutfit(data.outfit);
      } else {
          setError(data.detail || "Could not generate outfit.");
      }
    } catch (err) {
      console.error(err);
      setError("Failed to reach styling engine.");
    }
    setLoading(false);
  };

  const handleTryOn = async () => {
      setTryOnLoading(true);
      try {
          const prompt = `${parseColor(outfit.top.primary_color).text} ${outfit.top.sub_category} and ${parseColor(outfit.bottom.primary_color).text} ${outfit.bottom.sub_category}`;
          const res = await fetch(`http://localhost:8000/try-on`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ prompt })
          });
          const data = await res.json();
          if (data.image_url) setTryOnImage(data.image_url);
      } catch (e) {
          console.error(e);
      }
      setTryOnLoading(false);
  };

  const handleLogout = () => {
    setSessionUserId(null);
    setWardrobe([]);
    setOutfit(null);
  };

  if (!sessionUserId) {
      return (
          <div className="app-container">
             <header className="app-header">
               <h1 className="app-title">StylAI</h1>
               <p className="app-subtitle">Your personal intelligent wardrobe</p>
             </header>
             <Auth onLogin={setSessionUserId} />
          </div>
      );
  }

  // Helper to extract hex code if it exists like "navy blue | #1a2b3c"
  const parseColor = (colorStr) => {
     if (!colorStr) return { text: "Unknown", hex: null };
     const parts = colorStr.split("|");
     return {
         text: parts[0].trim(),
         hex: parts.length > 1 ? parts[1].trim() : null
     };
  };

  return (
    <div className="app-container">
      <header className="app-header" style={{ position: 'relative' }}>
        <button onClick={handleLogout} style={{ position: 'absolute', right: 0, top: 0, background: 'transparent', border: '1px solid var(--glass-border)', color: 'white', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}>Sign Out</button>
        <h1 className="app-title">StylAI</h1>
        <p className="app-subtitle">Your personal intelligent wardrobe</p>
      </header>

      <div className="glass-card main-content">
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h2>My Digital Wardrobe</h2>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
             <select value={occasion} onChange={(e) => setOccasion(e.target.value)} style={{ padding: '0.8rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white', fontFamily: 'inherit' }}>
                 <option value="Casual">Casual</option>
                 <option value="Date Night">Date Night</option>
                 <option value="Gym">Gym</option>
                 <option value="Formal">Formal</option>
             </select>
             <input type="text" value={city} onChange={(e) => setCity(e.target.value)} placeholder="City" style={{ padding: '0.8rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white', width: '120px', fontFamily: 'inherit' }} />
             <button className="btn" onClick={generateOutfit} disabled={loading || wardrobe.length === 0}>
               {loading && !outfit ? 'AI Thinking...' : '✨ Style Me!'}
             </button>
          </div>
        </div>

        {error && (
            <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '12px', marginBottom: '2rem', color: '#fca5a5' }}>
                {error}
            </div>
        )}

        {outfit && (
          <div className="glass-card" style={{ marginBottom: '3rem', background: 'rgba(139, 92, 246, 0.05)', borderColor: 'var(--accent)' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--accent)' }}>🌟 Gemini AI Recommended Outfit 🌟</h3>
            <p style={{ textAlign: 'center', color: '#a5b4fc', fontStyle: 'italic', marginBottom: '2rem', fontSize: '1.1rem' }}>"{outfit.reason}"</p>
            <p style={{ textAlign: 'center', fontSize: '0.9rem', color: 'gray', marginTop: '-1.5rem', marginBottom: '2rem' }}>Weather in {city}: {outfit.weather}</p>
            
            <div className="outfit-showcase">
              <div className="outfit-item garment-card">
                <span className="garment-badge">Top</span>
                {outfit.top.image_url ? 
                     <img src={outfit.top.image_url} alt="Top" /> :
                     <div style={{height: '100%', display: 'flex', alignItems:'center', justifyContent:'center'}}>No Image</div>
                }
                <div className="garment-info">
                  <h4 style={{textTransform: 'capitalize'}}>{parseColor(outfit.top.primary_color).text} {outfit.top.sub_category}</h4>
                  <p>{outfit.top.fit} Fit • {outfit.top.color_temperature} Tone</p>
                </div>
              </div>
              <div className="outfit-item garment-card">
                 <span className="garment-badge">Bottom</span>
                {outfit.bottom.image_url ? 
                     <img src={outfit.bottom.image_url} alt="Bottom" /> :
                     <div style={{height: '100%', display: 'flex', alignItems:'center', justifyContent:'center'}}>No Image</div>
                }
                <div className="garment-info">
                  <h4 style={{textTransform: 'capitalize'}}>{parseColor(outfit.bottom.primary_color).text} {outfit.bottom.sub_category}</h4>
                  <p>{outfit.bottom.fit} Fit • {outfit.bottom.color_temperature} Tone</p>
                </div>
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '2.5rem' }}>
                <button className="btn" onClick={handleTryOn} disabled={tryOnLoading}>
                   {tryOnLoading ? 'Generating Virtual Try-On...' : '📸 Virtual Try-On'}
                </button>
            </div>
            
            {tryOnImage && (
                <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                    <img src={tryOnImage} alt="Virtual Try On" style={{ maxWidth: '100%', borderRadius: '12px', border: '2px solid var(--accent)', boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }} />
                </div>
            )}
          </div>
        )}

        <label className="drop-zone" style={{ display: 'block', marginBottom: '2rem' }}>
          <input type="file" style={{ display: 'none' }} onChange={handleUpload} accept="image/*" disabled={loading} />
          {loading && !outfit ? <h3>⚡ Scanning AI Elements...</h3> : (
            <>
              <h3 style={{ marginBottom: '0.5rem', color: 'var(--accent)' }}>+ Add to Wardrobe</h3>
              <p style={{ color: 'var(--text-muted)' }}>Upload a clothing photo and AI will extract the color, fit, and category</p>
            </>
          )}
        </label>

        <div className="wardrobe-grid">
          {wardrobe.map((item) => (
             <div className="garment-card" key={item.garment_id}>
             <button className="btn-remove" onClick={() => handleDelete(item.garment_id)} title="Remove Item">✕</button>
             <span className="garment-badge">{item.category}</span>
             {item.image_url ? 
                <img src={item.image_url} alt={item.sub_category} /> :
                <div style={{height: '100%', display: 'flex', alignItems:'center', justifyContent:'center'}}>No Image</div>
             }
             <div className="garment-info">
               <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                 {parseColor(item.primary_color).hex && (
                    <div style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: parseColor(item.primary_color).hex, border: '1px solid rgba(255,255,255,0.5)' }}></div>
                 )}
                 <h4 style={{textTransform: 'capitalize', margin: 0}}>{parseColor(item.primary_color).text} {item.sub_category}</h4>
               </div>
               <p>{item.fit} Fit • {item.color_temperature}</p>
             </div>
           </div>
          ))}
        </div>
        {wardrobe.length === 0 && !loading && (
             <div style={{textAlign: 'center', padding: '3rem', color: 'var(--text-muted)'}}>
                 Your wardrobe is empty. Upload some clothes above!
            </div>
        )}

      </div>
    </div>
  );
}

export default App;
