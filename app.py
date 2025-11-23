import streamlit as st
import google.generativeai as genai
from PIL import Image
from duckduckgo_search import DDGS
import os
import re
import time

# ---------------------------------------------------------
# 1. CSS & UI TASARIMI
# ---------------------------------------------------------
st.set_page_config(page_title="TradeMaster Cloud", layout="wide", page_icon="🦅")

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    
    /* Header */
    .pro-header {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        padding: 20px; border-bottom: 2px solid #3b82f6; border-radius: 12px;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;
    }
    
    /* Kartlar */
    .glass-card {
        background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px; padding: 20px; backdrop-filter: blur(10px); margin-bottom: 15px;
    }
    
    /* Bar Göstergesi */
    .meter-container {
        width: 100%; height: 20px; background-color: #334155; border-radius: 10px;
        margin-top: 10px; margin-bottom: 5px; overflow: hidden; position: relative;
    }
    .meter-fill {
        height: 100%; border-radius: 10px; transition: width 1s ease-in-out;
    }
    .meter-marker {
        position: absolute; top: 0; bottom: 0; width: 4px; background: white;
        box-shadow: 0 0 5px rgba(0,0,0,0.8); z-index: 2;
    }
    
    /* Buton */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #3b82f6); color: white; border: none; padding: 16px;
        font-weight: bold; border-radius: 8px; width: 100%; letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. AYARLAR
# ---------------------------------------------------------
# Deployment uyumlu olması için Secret File kontrolü (Hata vermesin diye try-except)
try:
    if os.path.exists("my_secret_key.txt"):
        with open("my_secret_key.txt", "r") as f: saved_key = f.read().strip()
    else: saved_key = ""
except: saved_key = ""

with st.sidebar:
    st.title("🦅 TradeMaster Cloud")
    api_key = st.text_input("API Key", value=saved_key, type="password")
    
    model_name = "gemini-1.5-flash"
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            models.sort(key=lambda x: "flash" not in x)
            model_name = st.selectbox("AI Model", models)
        except: pass
    
    st.markdown("---")
    analysis_mode = st.radio("Analiz Modu", ("Tek Coin", "Korelasyon (Çoklu)"))

# ---------------------------------------------------------
# 3. FONKSİYONLAR
# ---------------------------------------------------------
def get_macro_data():
    data = {"fg": "50", "calendar": "Veri Yok", "volume": "Bilinmiyor"}
    try:
        with DDGS() as ddgs:
            fg_res = list(ddgs.text("crypto fear and greed index value today", max_results=1))
            if fg_res: data["fg"] = fg_res[0]['body']
            
            cal_res = list(ddgs.text("key economic events finance calendar this week", max_results=2))
            if cal_res: data["calendar"] = " ".join([r['body'] for r in cal_res])
            
            vol_res = list(ddgs.text("total crypto market volume 24h analysis", max_results=1))
            if vol_res: data["volume"] = vol_res[0]['body']
    except: pass
    return data

# ---------------------------------------------------------
# 4. ARAYÜZ
# ---------------------------------------------------------
st.markdown("""
<div class='pro-header'>
    <div><h1 style='margin:0; font-size:1.5rem; color:white;'>GLOBAL MARKET CLOUD</h1></div>
    <div><span style='background:#10b981; color:black; padding:5px 12px; border-radius:20px; font-weight:bold; font-size:0.8rem;'>● SYSTEM ONLINE</span></div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    with st.expander("📸 Grafik Paneli", expanded=True):
        uploaded_files = st.file_uploader("Grafik Yükle", type=["jpg", "png"], accept_multiple_files=True)
        image_parts = []
        if uploaded_files:
            cols = st.columns(6)
            for i, f in enumerate(uploaded_files):
                img = Image.open(f)
                image_parts.append(img)
                with cols[i % 6]: st.image(img, use_container_width=True)

with col2:
    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
    coin_input = st.text_input("Varlık", placeholder="Otomatik Algıla")
    analyze_btn = st.button("SİSTEMİ ÇALIŞTIR 🚀")

# ---------------------------------------------------------
# 5. YENİLENMİŞ ANALİZ MOTORU (STATUS CONTAINER)
# ---------------------------------------------------------
if analyze_btn and api_key and image_parts:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    # İŞTE YENİ GÖRSEL EFEKT KISMI BURASI
    with st.status("📡 Sistem Verileri İşleniyor...", expanded=True) as status:
        
        st.write("🌍 1/4 Makro ekonomik veriler taranıyor...")
        macro = get_macro_data()
        time.sleep(1) # Efekt için kısa bekleme
        
        st.write("👁️ 2/4 Grafikler taranıyor ve formasyonlar çıkarılıyor...")
        target = coin_input if coin_input else "Crypto Assets"
        
        st.write("🧠 3/4 Yapay zeka stratejiyi kuruyor...")
        
        prompt = f"""
        Sen Fon Yöneticisisin. Girdiler:
        - KORKU: {macro['fg']}
        - HACİM: {macro['volume']}
        - TAKVİM: {macro['calendar']}
        - HEDEF: {target}
        
        Format:
        [FG_SCORE:0-100 arası sayı]
        [VOLUME_LEVEL:Yüksek/Orta]
        
        1. TAKVİM ANALİZİ (Kısa)
        2. TEKNİK STRATEJİ ({analysis_mode})
        3. ÖZET (🏁 Sonrası tek cümle)
        """
        
        try:
            response = model.generate_content([prompt] + image_parts)
            text = response.text
            
            st.write("✅ 4/4 Rapor oluşturuldu!")
            status.update(label="Analiz Tamamlandı!", state="complete", expanded=False)
            
            # --- PARSING ---
            fg_score = 50
            volume_level = "Nötr"
            
            match = re.search(r"FG_SCORE:\s*(\d+)", text)
            if match: fg_score = min(100, int(match.group(1)))
            
            clean_text = re.sub(r"\[.*?\]", "", text)
            parts = clean_text.split("🏁")
            main_rpt = parts[0]
            summary = parts[1] if len(parts) > 1 else ""

            # --- EKRAN ---
            st.markdown("### 🌡️ Piyasa Duyarlılığı")
            
            bar_color = "#f59e0b"
            if fg_score < 30: bar_color = "#ef4444"
            if fg_score > 70: bar_color = "#10b981"
            
            st.markdown(f"""
            <div class='glass-card'>
                <div style='display:flex; justify-content:space-between;'>
                    <span style='font-size:1.5rem; font-weight:bold; color:{bar_color}'>{fg_score}/100</span>
                </div>
                <div class='meter-container'>
                    <div class='meter-fill' style='width: {fg_score}%; background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);'></div>
                    <div class='meter-marker' style='left: {fg_score}%;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_rpt, col_cal = st.columns([2, 1])
            with col_rpt:
                st.markdown(f"<div style='background:#064e3b; padding:15px; border-radius:8px; margin-bottom:10px;'><h3>🚀 KARAR</h3>{summary}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='glass-card'>{main_rpt}</div>", unsafe_allow_html=True)
            with col_cal:
                st.info("Veriler anlık web taramasından alınmıştır.")

        except Exception as e:
            st.error(f"Hata: {e}")