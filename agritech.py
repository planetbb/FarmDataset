import streamlit as st
import pandas as pd
import google.generativeai as genai

# [중요] 1. 페이지 설정
st.set_page_config(page_title="AgriTech FarmPlanner", layout="wide")

# 2. 구글 시트 URL 설정 (gid 값은 주신 정보를 바탕으로 유지)
SHEET_URLS = {
    "crop": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=0&single=true&output=csv",
    "equipment": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=1783566142&single=true&output=csv",
    "process": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBlhAdJB-jJOr_MoBgELY-qNKC5yJcD-G2gL03WRVTdbfOqtdiq0jHOnA-UlPakXWjpOw8PeMUroLG/pub?gid=1120300035&single=true&output=csv"
}

# 3. 데이터 로딩 함수
@st.cache_data
def load_data(url, type="crop"):
    df = pd.read_csv(url)
    
    if type == "crop":
        df['Yield_Per_sqm_kg'] = pd.to_numeric(df['Yield_Per_sqm_kg'], errors='coerce')
        df['Avg_Price_Per_kg_USD'] = pd.to_numeric(df['Avg_Price_Per_kg_USD'], errors='coerce')
        df = df.dropna(subset=['Yield_Per_sqm_kg', 'Avg_Price_Per_kg_USD'])
    
    if type == "process":
        # 숫자 변환 (인력 계산용)
        for col in ['Auto_1_ManHour_per_sqm', 'Auto_2_ManHour_per_sqm', 'Auto_3_ManHour_per_sqm']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# --- 앱 메인 로직 시작 ---
st.title("🌱 AgriTech FarmPlanner & Scheduler")

# 데이터 로드
try:
    df_crop = load_data(SHEET_URLS["crop"], type="crop")
    df_equip = load_data(SHEET_URLS["equipment"], type="equipment")
    df_process = load_data(SHEET_URLS["process"], type="process")
    st.sidebar.success(f"✅ 데이터 로드 완료: 작물 {len(df_crop)}종 / 장비 {len(df_equip)}종")
except Exception as e:
    st.error(f"데이터 로딩 실패: {e}")
    st.stop()

# 사이드바: 사용자 입력
with st.sidebar:
    st.header("📍 농지 정보 입력")
    # Category_Type 필터 (Paddy, Greenhouse, Upland, Orchard)
    farm_type = st.selectbox("농지 형태 선택", df_crop['Category_Type'].unique())
    size_sqm = st.number_input("농지 면적 (sqm)", min_value=10, value=1000)
    auto_level = st.select_slider("자동화 수준 선택", options=[1, 2, 3])
    st.info(f"선택된 자동화 레벨: {auto_level}")

# 메인 화면 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    "🌱 Crop Recommendation", 
    "📅 Farm Scheduler", 
    "🚜 Equipment Info", 
    "📊 Data Explorer"
])

# --- Tab 1: Crop Recommendation ---
with tab1:
    st.subheader(f"🔍 {farm_type} 환경 추천 작물")
    # 선택한 카테고리에 맞는 작물 필터링
    recommended_crops = df_crop[df_crop['Category_Type'] == farm_type]
    
    if recommended_crops.empty:
        st.info(f"해당 카테고리({farm_type})에 등록된 작물 데이터가 없습니다.")
    else:
        for _, row in recommended_crops.iterrows():
            with st.expander(f"📌 추천 작물: {row['Crop_Name']}"):
                col1, col2, col3 = st.columns(3)
                est_revenue = row['Yield_Per_sqm_kg'] * size_sqm * row['Avg_Price_Per_kg_USD']
                
                col1.metric("예상 연 매출", f"${est_revenue:,.0f}")
                col2.metric("sqm당 수확량", f"{row['Yield_Per_sqm_kg']} kg")
                col3.metric("국가/지역", f"{row['Country']}")

# --- Tab 2: Farm Scheduler ---
with tab2:
    st.subheader("🗓️ 주간 작업 스케줄 및 인력 배치")
    if not recommended_crops.empty:
        selected_crop = st.selectbox("스케줄을 확인할 작물을 선택하세요", recommended_crops['Crop_Name'].unique())
        crop_schedule = df_process[df_process['Crop_Name'] == selected_crop]
        
        if not crop_schedule.empty:
            # 표시할 컬럼 설정 (Auto_Equipment 포함)
            cols_to_show = ['Process_Step', 'Work_Week_Start', 'Work_Week_End', f'Auto_{auto_level}_ManHour_per_sqm']
            
            # Auto 2, 3일 경우 해당 장비명 컬럼 추가 표시
            if auto_level >= 2:
                equipment_col = f'Auto_{auto_level}_Equipment'
                if equipment_col in crop_schedule.columns:
                    cols_to_show.insert(1, equipment_col)
            
            st.dataframe(crop_schedule[cols_to_show], use_container_width=True)
            
            # 인력 계산
            total_hours = crop_schedule[f'Auto_{auto_level}_ManHour_per_sqm'].sum() * size_sqm
            st.warning(f"💡 {selected_crop} 재배 시, 연간 총 예상 노동시간은 **{total_hours:,.1f} Man-Hour** 입니다.")
        else:
            st.write("해당 작물의 공정 데이터가 없습니다.")

# --- Tab 3: Equipment Info ---
with tab3:
    st.subheader("🚜 선택된 자동화 단계 장비 상세 정보")
    if auto_level > 1:
        # 현재 선택된 작물의 공정에 쓰이는 장비 리스트 추출
        if not recommended_crops.empty:
            current_crop_procs = df_process[df_process['Crop_Name'] == selected_crop]
            equip_list = current_crop_procs[f'Auto_{auto_level}_Equipment'].unique()
            
            # 장비 마스터 데이터에서 해당 장비 정보 매칭
            matched_equip = df_equip[df_equip['Item_Name'].isin(equip_list)]
            
            if not matched_equip.empty:
                st.write(f"자동화 레벨 {auto_level}에 필요한 주요 장비 리스트입니다.")
                st.table(matched_equip[['Item_Name', 'Unit_Price_USD', 'Operating_Cost_Hour_USD', 'Lifespan_Years']])
            else:
                st.info("장비 마스터 데이터에 등록된 매칭 정보가 없습니다.")
    else:
        st.write("Auto Level 1은 수동 작업 단계이므로 별도의 자동화 장비가 필요하지 않습니다.")

# --- Tab 4: Data Explorer ---
with tab4:
    st.subheader("📊 Master Data Explorer")
    data_choice = st.radio("조회할 시트 선택:", ["Crop Master", "Process Standard", "Equipment Facility"], horizontal=True)
    
    if data_choice == "Crop Master":
        st.dataframe(df_crop, use_container_width=True)
    elif data_choice == "Process Standard":
        st.dataframe(df_process, use_container_width=True)
    else:
        st.dataframe(df_equip, use_container_width=True)
