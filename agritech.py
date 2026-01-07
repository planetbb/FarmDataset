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
        if data_type == "process":
            for col in ['Auto_1_ManHour_per_sqm', 'Auto_2_ManHour_per_sqm', 'Auto_3_ManHour_per_sqm']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# 데이터 로드
df_crop = load_data(SHEET_URLS["crop"], data_type="crop")
df_equip = load_data(SHEET_URLS["equipment"], data_type="equipment")
df_process = load_data(SHEET_URLS["process"], data_type="process")

if df_crop.empty or df_equip.empty or df_process.empty:
    st.stop()

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("📍 농업 설정 (Farm Setup)")
    selected_country = st.selectbox("1) 국가 선택 (Country)", df_crop['Country'].unique())
    country_crops = df_crop[df_crop['Country'] == selected_country]
    selected_crop = st.selectbox("2) 작물 선택 (Crop)", country_crops['Crop_Name'].unique())
    size_sqm = st.number_input("3) 농지 면적 (Area, sqm)", min_value=10, value=1000, step=100)
    
    auto_options = ["1) Manual", "2) Semi-Auto", "3) Full-Auto"]
    auto_label = st.radio("4) 자동화 수준 (Automation)", auto_options)
    
    automation_level = auto_label.split(") ")[1]  # "Manual", "Semi-Auto", "Full-Auto"
    auto_level_idx = auto_options.index(auto_label) + 1  # 1, 2, 3 (정수)

# --- Fallback 로직 핵심 데이터 준비 ---
# 선택된 작물의 정보 조회 (Category_Type 포함)
crop_info_row = df_crop[df_crop['Crop_Name'] == selected_crop].iloc[0]
selected_category = crop_info_row['Category_Type']

# 1. 특정 작물 전용 공정 데이터 검색
display_process_df = df_process[df_process['Crop_Name'] == selected_crop]

# 2. 전용 데이터가 없으면 Category_Type(표준 모델)으로 Fallback
is_fallback = False
if display_process_df.empty:
    display_process_df = df_process[df_process['Crop_Name'] == selected_category]
    is_fallback = True

# 메인 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["📊 수익성 분석", "📅 작업 스케줄", "🚜 투입 장비", "🗂️ 마스터 데이터"])

# --- Tab 1: 수익성 분석 ---
with tab1:
    # 0. 기초 수익 지표 계산
    total_yield_kg = size_sqm * crop_info_row['Yield_Per_sqm_kg']
    total_revenue_usd = total_yield_kg * crop_info_row['Avg_Price_Per_kg_USD']

    st.markdown(f"### 📊 {selected_crop} 분석 리포트")
    m1, m2, m3 = st.columns(3)
    m1.metric("🌾 예상 수확량", f"{total_yield_kg:,.1f} kg")
    m2.metric("💰 예상 매출액", f"$ {total_revenue_usd:,.0f}")
    m3.metric("📍 설정 면적", f"{size_sqm:,.0f} sqm")

    st.markdown("---")

    # 2. 레벨별 비교 데이터 계산 (Fallback 데이터 기반)
    comparison_data = []
    levels = ["Manual", "Semi-Auto", "Full-Auto"]
    
    for i, label in enumerate(levels):
        level_num = i + 1
        mh_col = f'Auto_{level_num}_ManHour_per_sqm'
        eq_col = f'Auto_{level_num}_Equipment'
        
        total_mh = display_process_df[mh_col].sum() * size_sqm if mh_col in display_process_df.columns else 0
        
        total_capex = 0
        used_equips = []
        if eq_col in display_process_df.columns:
            used_equips = display_process_df[eq_col].dropna().unique().tolist()
            if level_num == 1 and not used_equips: used_equips = ['Hand Tool Kit']
            if not df_equip.empty:
                prices = pd.to_numeric(df_equip[df_equip['Item_Name'].isin(used_equips)]['Unit_Price_USD'], errors='coerce')
                total_capex = prices.sum()
        
        comparison_data.append({"Level": label, "Total_ManHour": total_mh, "Total_CAPEX": total_capex, "Equipment": ", ".join(used_equips) if used_equips else "N/A"})
    df_compare = pd.DataFrame(comparison_data)

    # 3. 그래프와 카드 레이아웃 (가로 병렬 배치)
    chart_col, info_col = st.columns([1, 1])

    with chart_col:
        st.write("#### 📈 효율성 비교 차트")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_compare['Level'], y=df_compare['Total_ManHour'], name='Man-Hours', marker_color='#5dade2', yaxis='y1'))
        fig.add_trace(go.Scatter(x=df_compare['Level'], y=df_compare['Total_CAPEX'], name='Investment', line=dict(color='#e74c3c', width=3), yaxis='y2'))
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", y=1.2),
            yaxis=dict(title="Hrs"),
            yaxis2=dict(overlaying="y", side="right", showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)

    with info_col:
        st.write("#### 📋 레벨별 상세 요약")
        for i, label in enumerate(levels):
            data = df_compare.iloc[i]
            is_selected = (label == automation_level)
            bg_color = "#F0F7FF" if is_selected else "#FFFFFF"
            border_color = "#2E86C1" if is_selected else "#D5D8DC"
            
            st.markdown(f"""
                <div style="background-color: {bg_color}; border: 1px solid {border_color}; padding: 10px 15px; border-radius: 8px; margin-bottom: 8px; color: #000;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 900; font-size: 1.1em;">{label} {"✅" if is_selected else ""}</span>
                        <span style="font-size: 0.85em; color: #555;">⏱️ {data['Total_ManHour']:,.1f} hr | 💰 $ {data['Total_CAPEX']:,.0f}</span>
                    </div>
                    <div style="font-size: 0.75em; color: #333; margin-top: 5px; border-top: 0.5px solid #EEE; padding-top: 3px;">
                        <b>🚜 장비:</b> {data['Equipment']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # 4. 하단 성과 인사이트
    if automation_level != "Manual":
        manual_mh = df_compare.iloc[0]['Total_ManHour']
        selected_mh = df_compare[df_compare['Level'] == automation_level]['Total_ManHour'].values[0]
        extra_capex = df_compare[df_compare['Level'] == automation_level]['Total_CAPEX'].values[0] - df_compare.iloc[0]['Total_CAPEX']
        
        if manual_mh > 0:
            reduction = (1 - selected_mh / manual_mh) * 100
            st.info(f"""
                💡 **{automation_level} 분석 결과:**
                * **노동력 절감:** 수동 대비 약 **{reduction:.1f}%** ({manual_mh - selected_mh:,.1f}시간) 절감
                * **추가 투자비:** 수동 대비 **$ {extra_capex:,.0f}** 추가 지출 필요
            """)

# --- Tab 2: 작업 스케줄 ---
with tab2:
    st.subheader(f"📅 {selected_crop} 작업 프로세스")
    if is_fallback:
        st.warning(f"ℹ️ {selected_crop} 전용 데이터가 없어 **{selected_category}** 표준 공정을 표시합니다.")
    
    if not display_process_df.empty:
        # 선택된 자동화 레벨에 맞는 장비 컬럼명 동적 생성
        target_equip_col = f'Auto_{auto_level_idx}_Equipment'
        
        # 표시할 컬럼 설정 (Work_Week_Start/End가 있으면 포함)
        cols_to_show = ['Process_Step']
        for c in ['Work_Week_Start', 'Work_Week_End', target_equip_col]:
            if c in display_process_df.columns:
                cols_to_show.append(c)
        
        st.dataframe(display_process_df[cols_to_show], use_container_width=True, hide_index=True)
    else:
        st.error("표시할 공정 데이터가 없습니다.")

# --- Tab 3: 투입 장비 명세 ---
with tab3:
    st.subheader(f"🚜 {automation_level} 레벨 투입 장비 상세")
    
    target_equip_col = f'Auto_{auto_level_idx}_Equipment'
    if target_equip_col in display_process_df.columns:
        used_equips = display_process_df[target_equip_col].dropna().unique()
        
        # 장비 마스터 데이터에서 정보 추출
        matched_equip = df_equip[df_equip['Item_Name'].isin(used_equips)]
        
        if not matched_equip.empty:
            # 카드 형태로 장비 정보 나열
            for _, row in matched_equip.iterrows():
                with st.expander(f"🔹 {row['Item_Name']} ({row['Category']})"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Unit Price", f"$ {row['Unit_Price_USD']:,.0f}")
                    c2.metric("Lifespan", f"{row['Lifespan_Years']} Years")
                    if 'Description' in row:
                        c3.write(f"**Note:** {row['Description']}")
            
            st.markdown("---")
            st.write("#### 📊 장비 요약 테이블")
            st.dataframe(matched_equip, use_container_width=True, hide_index=True)
        else:
            st.info("등록된 상세 장비 제원이 없습니다. 마스터 데이터를 확인해주세요.")

# --- Tab 4: 마스터 데이터 관리 ---
with tab4:
    st.header("🗂️ 데이터베이스 원본 확인")
    choice = st.radio("조회할 데이터 선택", ["Crop Master", "Process Standard", "Equipment Facility"], horizontal=True)
    
    if choice == "Crop Master":
        st.dataframe(df_crop, use_container_width=True)
    elif choice == "Process Standard":
        st.dataframe(df_process, use_container_width=True)
    else:
        st.dataframe(df_equip, use_container_width=True)
