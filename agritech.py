# 1. 페이지 설정
st.set_page_config(page_title="Farm Automation Simulator by Jinux", layout="wide")

# (중략: load_data 함수 및 데이터 로딩 로직은 동일)
# df_crop, df_equip, df_process 로드 완료 후...

# --- 4. 사이드바 설정 및 변수 추출 ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #3498db;">
            <p style="font-size: 1.1em; font-weight: bold; color: #2c3e50; margin-bottom: 5px;">Please select below</p>
            <p style="font-size: 28px; animation: blink 1s linear infinite; color: #3498db; margin: 0;">⬇️</p>
        </div>
        <style> @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.1; } 100% { opacity: 1; } } </style>
    """, unsafe_allow_html=True)
    
    countries = df_crop['Country'].unique() if 'Country' in df_crop.columns else []
    selected_country = st.selectbox("Country (국가)", countries)
    
    crops = df_crop[df_crop['Country'] == selected_country]['Crop_Name'].unique()
    selected_crop = st.selectbox("Crop (작물)", crops)
    size_sqm = st.number_input("Farm Size (농지 규모, sqm)", min_value=10, value=1000, step=100)
    
    auto_options = ["1) Manual", "2) Semi-Auto", "3) Full-Auto"]
    auto_label = st.radio("Auto Level (자동화 수준)", auto_options)
    automation_level = auto_label.split(") ")[1]
    auto_level_idx = auto_options.index(auto_label) + 1

# --- 5. 핵심 데이터 처리 로직 (source_name 정의 포함) ---
# 선택된 작물 정보 추출
crop_info_rows = df_crop[df_crop['Crop_Name'] == selected_crop]
if not crop_info_rows.empty:
    crop_info = crop_info_rows.iloc[0]
else:
    st.error("선택한 작물 정보를 찾을 수 없습니다.")
    st.stop()

# 공정 데이터 매칭 및 source_name 정의 (에러 발생 지점 수정)
display_process_df = df_process[df_process['Crop_Name'] == selected_crop]
source_name = selected_crop # 기본값 설정

if display_process_df.empty:
    cat_type = crop_info.get('Category_Type', 'Upland')
    rep_crop = {"Greenhouse": "Strawberry", "Orchard": "Apple", "Paddy": "Rice"}.get(cat_type, "Potato")
    display_process_df = df_process[df_process['Crop_Name'] == rep_crop]
    source_name = f"{rep_crop} (Representative Data)" # 매칭 실패 시 대체 데이터명

# --- 6. 메인 화면 및 탭 구성 ---
h1, h2 = st.columns([1, 8])
h1.markdown("<h1 style='font-size: 60px; margin: 0;'>🚜</h1>", unsafe_allow_html=True)
h2.title("Farm Automation Simulator")
h2.markdown(f"<p style='margin-top:-15px;'>by <b>Jinux</b></p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Profitability", "📅 Schedule", "🚜 Equipment"])

with tab1:
    # (수익 분석 로직: total_yield, total_rev 계산 및 차트 생성)
    # 생략된 부분은 이전의 안정화된 로직과 동일
    pass

with tab2:
    # NameError 방지: source_name이 위에서 반드시 정의됨
    st.subheader(f"📅 {selected_crop} Process ({source_name})")
    target_eq_col = f'Auto_{auto_level_idx}_Equipment'
    base_cols = ['Process_Step', 'Work_Week_Start', 'Work_Week_End']
    available_cols = [c for c in base_cols + [target_eq_col] if c in display_process_df.columns]
    
    if not display_process_df.empty:
        st.dataframe(display_process_df[available_cols], use_container_width=True, hide_index=True)
    else:
        st.warning("No process data available for this selection.")

with tab3:
    st.subheader(f"🚜 {automation_level} 투입 장비 명세")
    
    # [수정] 장비 컬럼 존재 여부 체크
    target_eq_col = f'Auto_{auto_level_idx}_Equipment'
    
    if target_eq_col in display_process_df.columns:
        eq_names = display_process_df[target_eq_col].dropna().unique()
        matched_equip = df_equip[df_equip['Item_Name'].isin(eq_names)]
        
        if not matched_equip.empty:
            st.dataframe(matched_equip, use_container_width=True, hide_index=True)
        else:
            st.info(f"💡 {automation_level} 레벨에 등록된 상세 장비 정보가 없습니다.")
    else:
        st.error(f"❌ 시트에 '{target_eq_col}' 컬럼이 없습니다.")
# --- 8. 하단 푸터 (한 줄 우측 정렬) ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(f"""
    <div style="text-align: right; color: #7f8c8d; font-size: 0.8em;">
        <b>Copyright 2024. Jinux. All rights reserved.</b> | Designed for AgriTech Efficiency Analysis | 📅 최신 업데이트: {datetime.now().strftime("%Y-%m-%d")} | 📧 Contact: <a href="mailto:JinuxDreams@gmail.com" style="color:#7f8c8d; text-decoration:none;">JinuxDreams@gmail.com</a>
    </div>
""", unsafe_allow_html=True)
