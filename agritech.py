import streamlit as st
import pandas as pd
import google.generativeai as genai

# [중요] 1. 페이지 설정은 무조건 맨 위에!
st.set_page_config(page_title="AgriTech FarmPlanner", layout="wide")

# 2. 구글 시트 URL 설정
SHEET_URLS = {
    "crop": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=0&single=true&output=csv",
    "equipment": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=1783566142&single=true&output=csv",
    "process": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=1120300035&single=true&output=csv"
}

# 3. 데이터 로딩 함수 (청소 로직 포함)
@st.cache_data
def load_data(url, type="crop"):
    df = pd.read_csv(url)
    
    # 작물 데이터일 경우에만 숫자 변환 및 필터링 수행
    if type == "crop":
        df['Yield_Per_sqm_kg'] = pd.to_numeric(df['Yield_Per_sqm_kg'], errors='coerce')
        df['Avg_Price_Per_kg_USD'] = pd.to_numeric(df['Avg_Price_Per_kg_USD'], errors='coerce')
        df = df.dropna(subset=['Yield_Per_sqm_kg', 'Avg_Price_Per_kg_USD'])
    
    # 공정 데이터일 경우 숫자 변환 (인력 계산용)
    if type == "process":
        for col in ['Auto_1_ManHour_per_sqm', 'Auto_2_ManHour_per_sqm', 'Auto_3_ManHour_per_sqm']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
    return df

# --- 앱 메인 로직 시작 ---
st.title("🌱 AgriTech FarmPlanner & Scheduler")

# 데이터 로드 시도
try:
    df_crop = load_data(SHEET_URLS["crop"], type="crop")
    df_equip = load_data(SHEET_URLS["equipment"], type="equipment")
    df_process = load_data(SHEET_URLS["process"], type="process")
    st.sidebar.success(f"✅ 유효 데이터 {len(df_crop)}건 로드 완료")
except Exception as e:
    st.error(f"데이터 로딩 실패: {e}")
    st.stop()

# 사이드바: 사용자 입력
with st.sidebar:
    st.header("📍 농지 정보 입력")
    country = st.selectbox("국가 선택", df_crop['Country'].unique())
    size_sqm = st.number_input("농지 면적 (sqm)", min_value=10, value=1000)
    auto_level = st.select_slider("자동화 수준", options=[1, 2, 3])

# 메인 화면: FarmPlanner
tab1, tab2 = st.tabs(["📊 FarmPlanner", "📅 FarmScheduler"])

with tab1:
    st.subheader(f"🔍 {country} 지역 추천 작물")
    recommended_crops = df_crop[df_crop['Country'] == country]
    
    if recommended_crops.empty:
        st.info("해당 국가의 데이터가 없습니다.")
    else:
        for index, row in recommended_crops.iterrows():
            with st.expander(f"📌 추천 작물: {row['Crop_Name']}"):
                col1, col2, col3 = st.columns(3)
                
                # 계산 (모두 숫자임이 보장됨)
                est_revenue = row['Yield_Per_sqm_kg'] * size_sqm * row['Avg_Price_Per_kg_USD']
                
                col1.metric("예상 연 매출", f"${est_revenue:,.0f}")
                col2.metric("sqm당 수확량", f"{row['Yield_Per_sqm_kg']} kg")
                col3.metric("재배 난이도", f"⭐ {row['Difficulty_Level']}/5")

with tab2:
    st.subheader("🗓️ 주간 작업 스케줄 및 인력 배치")
    # 추천된 작물이 있을 때만 선택박스 표시
    if not recommended_crops.empty:
        selected_crop = st.selectbox("스케줄을 확인할 작물을 선택하세요", recommended_crops['Crop_Name'].unique())
        crop_schedule = df_process[df_process['Crop_Name'] == selected_crop]
        
        if not crop_schedule.empty:
            st.dataframe(crop_schedule[['Process_Name', 'Work_Week_Start', 'Work_Week_End', f'Auto_{auto_level}_ManHour_per_sqm']])
            
            # 인력 계산
            total_hours = crop_schedule[f'Auto_{auto_level}_ManHour_per_sqm'].sum() * size_sqm
            st.warning(f"💡 선택하신 자동화 레벨 {auto_level} 적용 시, 연간 총 예상 노동시간은 **{total_hours:,.1f} Man-Hour** 입니다.")
        else:
            st.write("해당 작물의 상세 공정 데이터가 아직 시트에 없습니다.")
