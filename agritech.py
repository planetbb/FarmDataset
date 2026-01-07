import streamlit as st  # <-- 이 부분이 반드시 최상단에 있어야 합니다.
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Farm Automation Simulator by Jinux", layout="wide")

# 2. 데이터 로딩 함수
@st.cache_data
def load_data(url, data_type="crop"):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        if data_type == "crop":
            for c in ['Yield_Per_sqm_kg', 'Avg_Price_Per_kg_USD']:
                if c in df.columns: 
                    df[c] = df[c].astype(str).str.replace(r'[$,]', '', regex=True)
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        elif data_type == "process":
            for i in range(1, 4):
                col = f'Auto_{i}_ManHour_per_sqm'
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        elif data_type == "equipment":
            if 'Unit_Price_USD' in df.columns: 
                df['Unit_Price_USD'] = df['Unit_Price_USD'].astype(str).str.replace(r'[$,]', '', regex=True)
                df['Unit_Price_USD'] = pd.to_numeric(df['Unit_Price_USD'], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# 데이터 로드
SHEET_URLS = {
    "crop": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=0&single=true&output=csv",
    "equipment": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=1783566142&single=true&output=csv",
    "process": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=1120300035&single=true&output=csv"
}

df_crop = load_data(SHEET_URLS["crop"], "crop")
df_equip = load_data(SHEET_URLS["equipment"], "equipment")
df_process = load_data(SHEET_URLS["process"], "process")

if df_crop.empty: st.stop()

# --- 3. 사이드바 구성 ---
with st.sidebar:
    # 깜빡이는 안내문구
    st.markdown("""
        <div style="text-align: center; background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #3498db;">
            <p style="font-size: 1.1em; font-weight: bold; color: #2c3e50; margin-bottom: 5px;">Please select below</p>
            <p style="font-size: 28px; animation: blink 1s linear infinite; color: #3498db; margin: 0;">⬇️</p>
        </div>
        <style> @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.1; } 100% { opacity: 1; } } </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    selected_country = st.selectbox("Country (국가)", df_crop['Country'].unique())
    selected_crop = st.selectbox("Crop (작물)", df_crop[df_crop['Country'] == selected_country]['Crop_Name'].unique())
    size_sqm = st.number_input("Farm Size (농지 규모, sqm)", min_value=10, value=1000, step=100)
    
    auto_label = st.radio("Auto Level (자동화 수준)", ["1) Manual", "2) Semi-Auto", "3) Full-Auto"])
    automation_level = auto_label.split(") ")[1]
    auto_idx = ["1) Manual", "2) Semi-Auto", "3) Full-Auto"].index(auto_label) + 1

    # Master Data View 버튼
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    st.subheader("🗂️ Master Data View")
    if 'db_view' not in st.session_state: st.session_state.db_view = None
    c1, c2 = st.columns(2)
    if c1.button("🌾 Crop", use_container_width=True): st.session_state.db_view = "작물"
    if c2.button("📅 Process", use_container_width=True): st.session_state.db_view = "공정"
    if st.button("🚜 Equipment", use_container_width=True): st.session_state.db_view = "장비"
    if st.session_state.db_view and st.button("❌ Close", use_container_width=True): st.session_state.db_view = None

# --- 4. 데이터 계산 로직 ---
crop_info = df_crop[df_crop['Crop_Name'] == selected_crop].iloc[0]
display_df = df_process[df_process['Crop_Name'] == selected_crop]
source_name = selected_crop
if display_df.empty:
    rep = {"Greenhouse": "Strawberry", "Orchard": "Apple", "Paddy": "Rice"}.get(crop_info['Category_Type'], "Potato")
    display_df = df_process[df_process['Crop_Name'] == rep]
    source_name = f"{rep} (Representative)"

# --- 5. 메인 화면 ---
h1, h2 = st.columns([1, 8])
h1.markdown("<h1 style='font-size: 60px; margin: 0;'>🚜</h1>", unsafe_allow_html=True)
h2.title("Farm Automation Simulator")
h2.markdown(f"<p style='margin-top:-15px;'>by <b>Jinux</b></p>", unsafe_allow_html=True)

if st.session_state.db_view:
    with st.expander(f"🔍 {st.session_state.db_view} Master Data", expanded=True):
        if st.session_state.db_view == "작물": st.dataframe(df_crop, use_container_width=True)
        elif st.session_state.db_view == "공정": st.dataframe(df_process, use_container_width=True)
        elif st.session_state.db_view == "장비": st.dataframe(df_equip, use_container_width=True)

tab1, tab2, tab3 = st.tabs(["📊 Profitability", "📅 Schedule", "🚜 Equipment"])

with tab1:
    total_yield = size_sqm * crop_info['Yield_Per_sqm_kg']
    total_rev = total_yield * crop_info['Avg_Price_Per_kg_USD']
    m1, m2, m3 = st.columns(3)
    m1.metric("🌾 예상 수확량", f"{total_yield:,.1f} kg")
    m2.metric("💰 예상 매출액", f"$ {total_rev:,.0f}")
    m3.metric("📍 설정 면적", f"{size_sqm:,.0f} sqm")
    
    comp_data = []
    for i, label in enumerate(["Manual", "Semi-Auto", "Full-Auto"]):
        n = i + 1
        mh = display_df[f'Auto_{n}_ManHour_per_sqm'].sum() * size_sqm if f'Auto_{n}_ManHour_per_sqm' in display_df.columns else 0
        eqs = display_df[f'Auto_{n}_Equipment'].dropna().unique().tolist() if f'Auto_{n}_Equipment' in display_df.columns else []
        cp = df_equip[df_equip['Item_Name'].isin(eqs)]['Unit_Price_USD'].sum()
        comp_data.append({"Level": label, "MH": mh, "CAPEX": cp})
    df_comp = pd.DataFrame(comp_data)

    l, r = st.columns([1, 1])
    with l:
        st.markdown('<div style="text-align:center; font-size:0.8em; font-weight:bold;"><span style="color:#D3D3D3;">■ Labor</span> <span style="color:#e74c3c;">— CAPEX</span></div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_comp['Level'], y=df_comp['MH'], marker_color=['#FFD700' if lvl == automation_level else '#D3D3D3' for lvl in df_comp['Level']], yaxis='y1'))
        fig.add_trace(go.Scatter(x=df_comp['Level'], y=df_comp['CAPEX'], line=dict(color='#e74c3c', width=3), yaxis='y2'))
        fig.update_layout(height=350, showlegend=False, margin=dict(l=0,r=0,t=10,b=0), yaxis2=dict(overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig, use_container_width=True)
    with r:
        for _, row in df_comp.iterrows():
            is_sel = (row['Level'] == automation_level)
            st.markdown(f"<div style='border:1px solid #ddd; padding:8px; border-radius:5px; margin-bottom:5px; background-color:{'#FFF9C4' if is_sel else '#FFF'}; color:#000;'><b>{row['Level']}</b>: {row['MH']:,.1f}h | ${row['CAPEX']:,.0f}</div>", unsafe_allow_html=True)

with tab2:
    st.subheader(f"📅 {selected_crop} Schedule ({source_name})")
    cols = [c for c in ['Process_Step', 'Work_Week_Start', f'Auto_{auto_idx}_Equipment'] if c in display_df.columns]
    st.dataframe(display_df[cols], use_container_width=True, hide_index=True)

with tab3:
    st.subheader(f"🚜 {automation_level} Equipment List")
    eq_col = f'Auto_{auto_idx}_Equipment'
    if eq_col in display_df.columns:
        names = display_df[eq_col].dropna().unique()
        st.dataframe(df_equip[df_equip['Item_Name'].isin(names)], use_container_width=True, hide_index=True)

# --- 6. 푸터 ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(f"""
    <div style="text-align: right; color: #7f8c8d; font-size: 0.8em;">
        <b>Copyright 2024. Jinux. All rights reserved.</b> | Designed for AgriTech Efficiency Analysis | 📅 최신 업데이트: {datetime.now().strftime("%Y-%m-%d")} | 📧 Contact: <a href="mailto:JinuxDreams@gmail.com" style="color:#7f8c8d; text-decoration:none;">JinuxDreams@gmail.com</a>
    </div>
""", unsafe_allow_html=True)
