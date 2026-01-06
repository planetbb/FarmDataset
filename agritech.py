import streamlit as st
import pandas as pd

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
    df = pd.read_csv(url)
    # 컬럼명 앞뒤 공백 제거 (안전장치)
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

# --- 메인 실행부 ---
st.title("🌱 AgriTech FarmPlanner & Scheduler")

try:
    df_crop = load_data(SHEET_URLS["crop"], data_type="crop")
    df_equip = load_data(SHEET_URLS["equipment"], data_type="equipment")
    df_process = load_data(SHEET_URLS["process"], data_type="process")
    st.sidebar.success("✅ 데이터 로드 성공")
except Exception as e:
    st.error(f"데이터 로딩 중 에러 발생: {e}")
    st.stop()

# 사이드바 입력
with st.sidebar:
    st.header("📍 농지 정보 입력")
    # Crop_Master의 컬럼명인 'Category'를 사용합니다.
    farm_type = st.selectbox("농지 형태 선택", df_crop['Category'].unique())
    size_sqm = st.number_input("농지 면적 (sqm)", min_value=10, value=1000)
    auto_level = st.select_slider("자동화 수준 선택", options=[1, 2, 3])

# 메인 탭
tab1, tab2, tab3, tab4 = st.tabs(["🌱 추천", "🗓️ 스케줄러", "🚜 장비정보", "📊 데이터뷰"])

# --- Tab 1: 추천 ---
with tab1:
    st.subheader(f"🔍 {farm_type} 환경 추천 작물")
    # 'Category' 컬럼으로 필터링
    recommended_crops = df_crop[df_crop['Category'] == farm_type]
    
    if recommended_crops.empty:
        st.info("해당 카테고리에 데이터가 없습니다.")
    else:
        for _, row in recommended_crops.iterrows():
            with st.expander(f"📌 {row['Crop_Name']}"):
                col1, col2 = st.columns(2)
                revenue = row['Yield_Per_sqm_kg'] * size_sqm * row['Avg_Price_Per_kg_USD']
                col1.metric("예상 매출", f"${revenue:,.0f}")
                col2.metric("지역", row['Country'])

# --- Tab 2: 스케줄러 ---
with tab2:
    if not recommended_crops.empty:
        selected_crop = st.selectbox("작물 선택", recommended_crops['Crop_Name'].unique())
        crop_schedule = df_process[df_process['Crop_Name'] == selected_crop]
        
        if not crop_schedule.empty:
            show_cols = ['Process_Step', 'Work_Week_Start', 'Work_Week_End', f'Auto_{auto_level}_ManHour_per_sqm']
            if auto_level >= 2:
                equip_col = f'Auto_{auto_level}_Equipment'
                if equip_col in crop_schedule.columns:
                    show_cols.insert(1, equip_col)
            st.dataframe(crop_schedule[show_cols], use_container_width=True)
            
            total_h = crop_schedule[f'Auto_{auto_level}_ManHour_per_sqm'].sum() * size_sqm
            st.warning(f"💡 연간 총 예상 노동시간: {total_h:,.1f} Man-Hour")

# --- Tab 3: 장비정보 ---
with tab3:
    if auto_level > 1 and not recommended_crops.empty:
        equip_names = df_process[df_process['Crop_Name'] == selected_crop][f'Auto_{auto_level}_Equipment'].unique()
        matched = df_equip[df_equip['Item_Name'].isin(equip_names)]
        if not matched.empty:
            st.table(matched[['Item_Name', 'Unit_Price_USD', 'Operating_Cost_Hour_USD']])
        else:
            st.info("장비 마스터 정보가 없습니다.")
    else:
        st.write("자동화 레벨 1은 장비 정보가 표시되지 않습니다.")

# --- Tab 4: 데이터뷰 ---
with tab4:
    choice = st.radio("시트 선택", ["작물", "공정", "장비"], horizontal=True)
    if choice == "작물": st.dataframe(df_crop)
    elif choice == "공정": st.dataframe(df_process)
    else: st.dataframe(df_equip)
