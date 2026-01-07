import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="AgriTech FarmPlanner", layout="wide")

# 2. 구글 시트 URL 설정
SHEET_URLS = {
    "crop": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=0&single=true&output=csv",
    "equipment": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=1783566142&single=true&output=csv",
    "process": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=1120300035&single=true&output=csv"
}

# 3. 데이터 로딩 함수
@st.cache_data
def load_data(url, data_type="crop"):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        
        if data_type == "crop":
            df['Yield_Per_sqm_kg'] = pd.to_numeric(df['Yield_Per_sqm_kg'], errors='coerce')
            df['Avg_Price_Per_kg_USD'] = pd.to_numeric(df['Avg_Price_Per_kg_USD'], errors='coerce')
            df = df.dropna(subset=['Yield_Per_sqm_kg', 'Avg_Price_Per_kg_USD'])
        
        if data_type == "process":
            for col in ['Auto_1_ManHour_per_sqm', 'Auto_2_ManHour_per_sqm', 'Auto_3_ManHour_per_sqm']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패 ({data_type}): {e}")
        return pd.DataFrame()

# --- 메인 실행부 ---
st.title("🌱 AgriTech FarmPlanner & Scheduler")

df_crop = load_data(SHEET_URLS["crop"], data_type="crop")
df_equip = load_data(SHEET_URLS["equipment"], data_type="equipment")
df_process = load_data(SHEET_URLS["process"], data_type="process")

if df_crop.empty or df_equip.empty or df_process.empty:
    st.error("데이터를 불러올 수 없습니다. URL 및 시트 설정을 확인해주세요.")
    st.stop()

# --- 사이드바: 입력 인터페이스 ---
with st.sidebar:
    st.header("📍 농업 설정 (Farm Setup)")
    selected_country = st.selectbox("1) 국가 선택 (Country)", df_crop['Country'].unique())
    country_crops = df_crop[df_crop['Country'] == selected_country]
    selected_crop = st.selectbox("2) 작물 선택 (Crop)", country_crops['Crop_Name'].unique())
    size_sqm = st.number_input("3) 농지 면적 (Area, sqm)", min_value=10, value=1000, step=100)
    
    auto_mapping = {"1) Manual": "Manual", "2) Semi-Auto": "Semi-Auto", "3) Full-Auto": "Full-Auto"}
    auto_label = st.radio("4) 자동화 수준 (Automation)", list(auto_mapping.keys()))
    # [핵심 수정] 아래 변수명이 tab1의 표 출력 로직과 일치해야 함
    automation_level = auto_mapping[auto_label] 
    auto_level_num = list(auto_mapping.keys()).index(auto_label) + 1

# 메인 탭 설정
tab1, tab2, tab3, tab4 = st.tabs(["📊 수익성 분석", "📅 작업 스케줄", "🚜 투입 장비", "🗂️ 마스터 데이터"])

# --- 수익성 분석 섹션 (Tab 1) ---
with tab1:
    st.header(f"📊 {selected_crop} 자동화 레벨별 비교 분석")
    comparison_data = []
    crop_schedule = df_process[df_process['Crop_Name'] == selected_crop]
    
    if not crop_schedule.empty:
        for level in [1, 2, 3]:
            label = ["Manual", "Semi-Auto", "Full-Auto"][level-1]
            mh_col = f'Auto_{level}_ManHour_per_sqm'
            eq_col = f'Auto_{level}_Equipment'
            
            total_mh = crop_schedule[mh_col].sum() * size_sqm if mh_col in crop_schedule.columns else 0
            
            total_capex = 0
            if eq_col in crop_schedule.columns:
                used_equips = crop_schedule[eq_col].dropna().unique()
                if level == 1 and len(used_equips) == 0:
                    used_equips = ['Hand Tool Kit']
                
                if not df_equip.empty:
                    p_col = 'Unit_Price_USD' 
                    name_col = 'Item_Name'
                    if p_col in df_equip.columns and name_col in df_equip.columns:
                        # [이 줄의 들여쓰기를 확인하세요! 앞선 if보다 4칸 더 들어가야 합니다]
                        prices = pd.to_numeric(df_equip[df_equip[name_col].isin(used_equips)][p_col], errors='coerce')
                        total_capex = prices.sum()
                    else:
                        # 컬럼이 없을 경우 처리
                        total_capex = 0
