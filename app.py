import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

st.set_page_config(
    page_title="컬러 매칭 데이터 입력",
    layout="wide"
)

SHEET_NAME = "color_data_v2"
WORKSHEET_NAME = "data"

COLUMNS = [
    "sample_id", "color_name", "base_type",
    "clear_base_g", "white_base_g",
    "iron_yellow_g", "iron_black_g", "iron_red_g",
    "IOR_g", "TiO2_g", "panax_green_g", "cyanine_blue_g",
    "f38red_g", "yellow65_g",
    "L_avg", "a_avg", "b_avg",
    "aggregate", "mixing_time", "date", "remarks", "created_at"
]

@st.cache_resource
def connect_gsheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(credentials)
    worksheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
    return worksheet

def load_data(worksheet):
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(records)

def append_row(worksheet, row_dict):
    row = [row_dict.get(col, "") for col in COLUMNS]
    worksheet.append_row(row, value_input_option="USER_ENTERED")

st.title("컬러 매칭 데이터 입력 시스템")
st.caption("2차 버전 컬러 매칭 데이터 저장용 Streamlit 앱")

try:
    worksheet = connect_gsheet()
    df_existing = load_data(worksheet)
except Exception as e:
    st.error("구글시트 연결에 실패했습니다.")
    st.exception(e)
    st.stop()

with st.form("color_form"):
    st.subheader("기본 정보")

    col1, col2, col3 = st.columns(3)

    with col1:
        sample_id = st.text_input("Sample ID *")

    with col2:
        color_name = st.text_input("Color Name *")

    with col3:
        base_type = st.selectbox("Base Type", ["Clear", "White"])

    st.subheader("수지 / 베이스 투입량")

    col1, col2 = st.columns(2)

    with col1:
        clear_base_g = st.number_input(
            "Clear Base (g)",
            min_value=0.0,
            step=0.01,
            format="%.2f"
        )

    with col2:
        white_base_g = st.number_input(
            "White Base (g)",
            min_value=0.0,
            step=0.01,
            format="%.2f"
        )

    st.subheader("안료 / 토너 투입량")

    col1, col2, col3 = st.columns(3)

    with col1:
        iron_yellow_g = st.number_input("Iron Yellow (g)", min_value=0.0, step=0.01, format="%.2f")
        iron_black_g = st.number_input("Iron Black (g)", min_value=0.0, step=0.01, format="%.2f")
        iron_red_g = st.number_input("Iron Red (g)", min_value=0.0, step=0.01, format="%.2f")

    with col2:
        IOR_g = st.number_input("IOR (g)", min_value=0.0, step=0.01, format="%.2f")
        TiO2_g = st.number_input("TiO2 (g)", min_value=0.0, step=0.01, format="%.2f")
        panax_green_g = st.number_input("Panax Green (g)", min_value=0.0, step=0.01, format="%.2f")

    with col3:
        cyanine_blue_g = st.number_input("Cyanine Blue (g)", min_value=0.0, step=0.01, format="%.2f")
        f38red_g = st.number_input("F38 Red (g)", min_value=0.0, step=0.01, format="%.2f")
        yellow65_g = st.number_input("Yellow 65 (g)", min_value=0.0, step=0.01, format="%.2f")

    st.subheader("측정 Lab 값")

    col1, col2, col3 = st.columns(3)

    with col1:
        L_avg = st.number_input("L_avg", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")

    with col2:
        a_avg = st.number_input("a_avg", min_value=-128.0, max_value=127.0, step=0.01, format="%.2f")

    with col3:
        b_avg = st.number_input("b_avg", min_value=-128.0, max_value=127.0, step=0.01, format="%.2f")

    st.subheader("기타 조건")

    col1, col2, col3 = st.columns(3)

    with col1:
        aggregate = st.selectbox("Aggregate", [0, 1])

    with col2:
        mixing_time = st.text_input("Mixing Time", value="2min")

    with col3:
        input_date = st.date_input("Date", value=date.today())

    remarks = st.text_area("Remarks")

    submitted = st.form_submit_button("저장하기")

if submitted:
    errors = []

    if not sample_id.strip():
        errors.append("Sample ID는 필수입니다.")

    if not color_name.strip():
        errors.append("Color Name은 필수입니다.")

    if clear_base_g > 0 and white_base_g > 0:
        errors.append("Clear Base와 White Base는 동시에 입력하지 않는 것을 권장합니다.")

    pigment_values = {
        "iron_yellow_g": iron_yellow_g,
        "iron_black_g": iron_black_g,
        "iron_red_g": iron_red_g,
        "IOR_g": IOR_g,
        "TiO2_g": TiO2_g,
        "panax_green_g": panax_green_g,
        "cyanine_blue_g": cyanine_blue_g,
        "f38red_g": f38red_g,
        "yellow65_g": yellow65_g,
    }

    used_pigments = [name for name, value in pigment_values.items() if value > 0]

    if len(used_pigments) == 0:
        errors.append("최소 1개 이상의 안료/토너를 입력해야 합니다.")

    if len(used_pigments) > 3:
        errors.append("안료/토너는 3개 이하 입력을 권장합니다.")

    if "sample_id" in df_existing.columns:
        existing_ids = df_existing["sample_id"].astype(str).tolist()
        if sample_id.strip() in existing_ids:
            errors.append(f"이미 존재하는 Sample ID입니다: {sample_id}")

    if errors:
        for error in errors:
            st.error(error)
    else:
        row_dict = {
            "sample_id": sample_id.strip(),
            "color_name": color_name.strip(),
            "base_type": base_type,
            "clear_base_g": clear_base_g,
            "white_base_g": white_base_g,
            "iron_yellow_g": iron_yellow_g,
            "iron_black_g": iron_black_g,
            "iron_red_g": iron_red_g,
            "IOR_g": IOR_g,
            "TiO2_g": TiO2_g,
            "panax_green_g": panax_green_g,
            "cyanine_blue_g": cyanine_blue_g,
            "f38red_g": f38red_g,
            "yellow65_g": yellow65_g,
            "L_avg": L_avg,
            "a_avg": a_avg,
            "b_avg": b_avg,
            "aggregate": aggregate,
            "mixing_time": mixing_time,
            "date": input_date.strftime("%Y-%m-%d"),
            "remarks": remarks,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        append_row(worksheet, row_dict)

        st.success("저장 완료!")
        st.write("저장된 데이터")
        st.dataframe(pd.DataFrame([row_dict]), use_container_width=True)

st.divider()
st.subheader("최근 저장 데이터")

df_latest = load_data(worksheet)

if len(df_latest) > 0:
    st.dataframe(df_latest.tail(10), use_container_width=True)
else:
    st.info("아직 저장된 데이터가 없습니다.")
