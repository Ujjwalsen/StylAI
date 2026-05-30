import React, { useState, useEffect } from 'react';
import './index.css';

function App() {
  const [wardrobe, setWardrobe] = useState([]);
  const [outfit, setOutfit] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Dummy User ID for MVPI
  const USER_ID = 1;

  useEffect(() => {
    fetchWardrobe();
  }, []);

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
    try {
      const res = await fetch(`http://localhost:8000/style/${USER_ID}`);
      const data = await res.json();
      if (data.outfit) {
        setOutfit(data.outfit);
      } else {
          setError(data.detail || "Could not generate outfit.");
      }
    } catch (err) {
      console.error(err);
      setError("Failed to reach styling engine. Make sure you have both tops and bottoms!");
    }
    setLoading(false);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">StylAI</h1>
        <p className="app-subtitle">Your personal intelligent wardrobe</p>
      </header>

      <div className="glass-card main-content">
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h2>My Digital Wardrobe</h2>
          <button className="btn" onClick={generateOutfit} disabled={loading || wardrobe.length === 0}>
            {loading && !outfit ? 'AI Thinking...' : '✨ Style Me!'}
          </button>
        </div>

        {error && (
            <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '12px', marginBottom: '2rem', color: '#fca5a5' }}>
                {error}
            </div>
        )}

        {outfit && (
          <div className="glass-card" style={{ marginBottom: '3rem', background: 'rgba(139, 92, 246, 0.05)', borderColor: 'var(--accent)' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--accent)' }}>🌟 AI Recommended Outfit (Match Score: {outfit.score}/10) 🌟</h3>
            <div className="outfit-showcase">
              <div className="outfit-item garment-card">
                <span className="garment-badge">Top</span>
                {outfit.top.image_url ? 
                     <img src={outfit.top.image_url} alt="Top" /> :
                     <div style={{height: '100%', display: 'flex', alignItems:'center', justifyContent:'center'}}>No Image</div>
                }
                <div className="garment-info">
                  <h4 style={{textTransform: 'capitalize'}}>{outfit.top.primary_color} {outfit.top.sub_category}</h4>
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
                  <h4 style={{textTransform: 'capitalize'}}>{outfit.bottom.primary_color} {outfit.bottom.sub_category}</h4>
                  <p>{outfit.bottom.fit} Fit • {outfit.bottom.color_temperature} Tone</p>
                </div>
              </div>
            </div>
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
               <h4 style={{textTransform: 'capitalize'}}>{item.primary_color} {item.sub_category}</h4>
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
