"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOVA시 스마트시티 그림형 정책 처치 시뮬레이션
simulation_story.py

이 앱은 최종 수치 결과를 계산하는 대시보드가 아니라,
예산·에너지 배분이라는 정책 처치가 도시 장면을 어떻게 바꾸는지
그림 중심으로 보여주는 1차 시뮬레이션 앱입니다.

실행:
streamlit run simulation_story.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import time
import urllib.parse
import streamlit as st

# ==================================================
# 페이지 설정
# ==================================================
st.set_page_config(
    page_title="NOVA시 정책 처치 시뮬레이션",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================
# CSS
# ==================================================
st.markdown(
    """
    <style>
    .stApp {
        background: #ffffff;
        color: #1f2328;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f6f8fa 0%, #ffffff 100%);
        border-right: 1px solid #d0d7de;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #1f2328 !important;
    }

    .hero {
        background: linear-gradient(135deg, #0969da 0%, #8250df 100%);
        border-radius: 28px;
        padding: 42px 46px;
        color: white;
        margin-bottom: 28px;
        box-shadow: 0 18px 42px rgba(9,105,218,0.22);
    }

    .hero .eyebrow {
        font-size: 13px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 900;
        opacity: 0.9;
        margin-bottom: 10px;
    }

    .hero .title {
        font-size: 42px;
        font-weight: 950;
        line-height: 1.18;
        margin-bottom: 14px;
    }

    .hero .subtitle {
        font-size: 17px;
        line-height: 1.75;
        opacity: 0.96;
        max-width: 1050px;
    }

    .pill-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 22px;
    }

    .pill {
        background: rgba(255,255,255,0.17);
        border: 1px solid rgba(255,255,255,0.28);
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 13px;
        font-weight: 800;
    }

    .notice-card {
        background: #fff8c5;
        border: 1px solid #f0d66b;
        border-radius: 18px;
        padding: 18px 20px;
        color: #1f2328;
        line-height: 1.7;
        font-size: 14px;
        margin-bottom: 20px;
    }

    .stage-card {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 24px;
        padding: 26px 28px;
        box-shadow: 0 12px 28px rgba(27,31,36,0.07);
        margin-bottom: 22px;
    }

    .stage-title {
        font-size: 28px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 8px;
    }

    .stage-desc {
        font-size: 15px;
        color: #57606a;
        line-height: 1.75;
        margin-bottom: 16px;
    }

    .process-wrap {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin: 18px 0 22px;
    }

    .process-step {
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 16px 14px;
        text-align: center;
        min-height: 130px;
    }

    .process-step.active {
        background: linear-gradient(135deg, #ddf4ff 0%, #f6f8fa 100%);
        border: 2px solid #0969da;
        box-shadow: 0 10px 26px rgba(9,105,218,0.15);
    }

    .process-icon {
        font-size: 30px;
        margin-bottom: 8px;
    }

    .process-title {
        font-size: 14px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 6px;
    }

    .process-desc {
        font-size: 12px;
        color: #57606a;
        line-height: 1.45;
    }

    .city-scene {
        background: linear-gradient(180deg, #ddf4ff 0%, #ffffff 42%, #f0fff4 100%);
        border: 1px solid #d0d7de;
        border-radius: 28px;
        padding: 24px;
        margin-top: 18px;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.6);
    }

    .city-sky {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }

    .city-title {
        font-size: 20px;
        font-weight: 950;
        color: #1f2328;
    }

    .city-weather {
        font-size: 30px;
    }

    .city-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
        margin-top: 12px;
    }

    .district-zone {
        background: rgba(255,255,255,0.88);
        border: 1px solid #d0d7de;
        border-radius: 22px;
        padding: 16px 14px;
        min-height: 210px;
        box-shadow: 0 8px 20px rgba(27,31,36,0.06);
    }

    .district-name {
        font-size: 14px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 8px;
        text-align: center;
    }

    .district-sub {
        font-size: 12px;
        color: #57606a;
        line-height: 1.45;
        text-align: center;
        margin-bottom: 10px;
    }

    .icon-field {
        background: #f6f8fa;
        border: 1px dashed #d0d7de;
        border-radius: 16px;
        padding: 12px 10px;
        min-height: 118px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-content: flex-start;
        justify-content: center;
    }

    .scene-icon {
        font-size: 28px;
        display: inline-block;
        animation: popIn 0.55s ease both;
    }

    @keyframes popIn {
        0% { transform: scale(0.55); opacity: 0; }
        70% { transform: scale(1.12); opacity: 1; }
        100% { transform: scale(1); opacity: 1; }
    }

    .policy-board {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 24px;
        padding: 22px 24px;
        box-shadow: 0 10px 26px rgba(27,31,36,0.07);
        height: 100%;
    }

    .board-title {
        font-size: 20px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 12px;
    }

    .board-desc {
        font-size: 14px;
        color: #57606a;
        line-height: 1.65;
        margin-bottom: 14px;
    }

    .treatment-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 14px;
    }

    .treatment-card {
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 16px 14px;
        text-align: center;
        min-height: 160px;
    }

    .treatment-card .big-icon {
        font-size: 36px;
        margin-bottom: 8px;
    }

    .treatment-card .label {
        font-size: 15px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 6px;
    }

    .treatment-card .value {
        font-size: 28px;
        font-weight: 950;
        color: #0969da;
        margin-bottom: 4px;
    }

    .treatment-card .explain {
        font-size: 12px;
        color: #57606a;
        line-height: 1.45;
    }

    .effect-strip {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin: 18px 0;
    }

    .effect-item {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 16px 14px;
        text-align: center;
        box-shadow: 0 8px 18px rgba(27,31,36,0.05);
    }

    .effect-icon {
        font-size: 34px;
        margin-bottom: 8px;
    }

    .effect-title {
        font-size: 14px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 5px;
    }

    .effect-desc {
        font-size: 12px;
        color: #57606a;
        line-height: 1.45;
    }

    .energy-field {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-top: 16px;
    }

    .energy-zone {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 22px;
        padding: 18px 16px;
        text-align: center;
        min-height: 220px;
        box-shadow: 0 8px 20px rgba(27,31,36,0.06);
    }

    .energy-title {
        font-size: 15px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 8px;
    }

    .energy-desc {
        font-size: 12px;
        color: #57606a;
        line-height: 1.5;
        margin-bottom: 12px;
    }

    .energy-icons {
        background: #f6f8fa;
        border: 1px dashed #d0d7de;
        border-radius: 16px;
        padding: 12px;
        min-height: 118px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        align-content: flex-start;
    }

    .transition-arrow {
        text-align: center;
        font-size: 44px;
        font-weight: 950;
        color: #0969da;
        margin: 8px 0 18px;
    }

    .final-scene-card {
        background: linear-gradient(135deg, #f0fff4 0%, #ddf4ff 100%);
        border: 1px solid #aceebb;
        border-radius: 26px;
        padding: 26px 28px;
        margin-top: 20px;
    }

    .final-title {
        font-size: 28px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 10px;
    }

    .final-desc {
        font-size: 15px;
        color: #57606a;
        line-height: 1.75;
    }

    .dashboard-link-card {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 22px;
        padding: 24px 26px;
        box-shadow: 0 10px 26px rgba(27,31,36,0.07);
        margin-top: 18px;
    }

    .dashboard-link-title {
        font-size: 22px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 8px;
    }

    .dashboard-link-desc {
        font-size: 14px;
        color: #57606a;
        line-height: 1.75;
        margin-bottom: 16px;
    }

    .dashboard-button {
        display: inline-block;
        background: #0969da;
        color: white !important;
        padding: 12px 18px;
        border-radius: 14px;
        text-decoration: none !important;
        font-weight: 900;
        font-size: 14px;
        box-shadow: 0 8px 18px rgba(9,105,218,0.22);
    }

    @media (max-width: 1100px) {
        .city-grid,
        .effect-strip,
        .energy-field,
        .process-wrap {
            grid-template-columns: 1fr;
        }

        .treatment-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==================================================
# 프리셋
# ==================================================
PRESETS = {
    "직접 입력": None,
    "초기 상태 (인프라 편중)": dict(
        welfare=15, education=15, energy_infra=10, general_infra=45, safety=15,
        solar=10, hydrogen=5, ess=5, external=80
    ),
    "복지 집중": dict(
        welfare=40, education=15, energy_infra=15, general_infra=20, safety=10,
        solar=25, hydrogen=15, ess=15, external=45
    ),
    "에너지 자립 집중": dict(
        welfare=12, education=10, energy_infra=45, general_infra=23, safety=10,
        solar=45, hydrogen=30, ess=20, external=5
    ),
    "균형 배분": dict(
        welfare=22, education=20, energy_infra=20, general_infra=23, safety=15,
        solar=35, hydrogen=25, ess=20, external=20
    ),
    "선순환 최적 ⭐": dict(
        welfare=20, education=18, energy_infra=30, general_infra=22, safety=10,
        solar=40, hydrogen=35, ess=20, external=5
    ),
}

# ==================================================
# 유틸 함수
# ==================================================
def icon_count(value, max_icons=12):
    if value <= 0:
        return 0
    return max(1, min(max_icons, round(value / 100 * max_icons)))


def icons(symbol, value, max_icons=12):
    count = icon_count(value, max_icons)
    return "".join([f'<span class="scene-icon">{symbol}</span>' for _ in range(count)])


def mixed_icons(items):
    html = ""
    for symbol, value, max_icons in items:
        html += icons(symbol, value, max_icons)
    return html


def build_query_string(
    preset_choice,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external
):
    params = {
        "preset": preset_choice,
        "welfare": welfare,
        "education": education,
        "energy_infra": energy_infra,
        "general_infra": general_infra,
        "safety": safety,
        "solar": solar,
        "hydrogen": hydrogen,
        "ess": ess,
        "external": external,
    }
    return urllib.parse.urlencode(params)


def get_dashboard_url_from_secrets():
    try:
        return st.secrets.get("DASHBOARD_URL", "")
    except Exception:
        return ""


# ==================================================
# 화면 조각 함수
# ==================================================
def show_process_map(active_step):
    steps = [
        (1, "🎛️", "정책 투입", "예산·에너지 배분 선택"),
        (2, "🏗️", "도시 시설 변화", "학교·병원·경찰·도로 증가"),
        (3, "⚡", "에너지 설비 변화", "태양광·수소·ESS 설비 배치"),
        (4, "🌆", "도시 장면 완성", "처치가 적용된 도시 모습"),
        (5, "📊", "상세 분석 이동", "2차 대시보드에서 결과 확인"),
    ]

    html = '<div class="process-wrap">'
    for num, icon, title, desc in steps:
        active_class = " active" if num == active_step else ""
        html += f"""
        <div class="process-step{active_class}">
            <div class="process-icon">{icon}</div>
            <div class="process-title">{num}. {title}</div>
            <div class="process-desc">{desc}</div>
        </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def show_budget_treatment_cards(welfare, education, energy_infra, general_infra, safety):
    st.markdown(
        f"""
        <div class="treatment-grid">
            <div class="treatment-card">
                <div class="big-icon">🏥</div>
                <div class="label">복지 예산</div>
                <div class="value">{welfare}%</div>
                <div class="explain">병원, 복지관, 돌봄센터가 늘어납니다.</div>
            </div>
            <div class="treatment-card">
                <div class="big-icon">🏫</div>
                <div class="label">교육 예산</div>
                <div class="value">{education}%</div>
                <div class="explain">학교, 학원, 도서관, 청년 교육 공간이 생깁니다.</div>
            </div>
            <div class="treatment-card">
                <div class="big-icon">🔌</div>
                <div class="label">에너지 인프라</div>
                <div class="value">{energy_infra}%</div>
                <div class="explain">충전소, 스마트그리드, 에너지 관리 시설이 늘어납니다.</div>
            </div>
            <div class="treatment-card">
                <div class="big-icon">🚌</div>
                <div class="label">일반 인프라</div>
                <div class="value">{general_infra}%</div>
                <div class="explain">도로, 버스, 공원, 생활SOC가 확충됩니다.</div>
            </div>
            <div class="treatment-card">
                <div class="big-icon">👮</div>
                <div class="label">안전 예산</div>
                <div class="value">{safety}%</div>
                <div class="explain">경찰, CCTV, 소방, 재난 대응 체계가 강화됩니다.</div>
            </div>
            <div class="treatment-card">
                <div class="big-icon">🎯</div>
                <div class="label">처치 방식</div>
                <div class="value">100%</div>
                <div class="explain">정해진 예산을 어디에 배분하느냐가 도시 장면을 바꿉니다.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_city_scene(welfare, education, energy_infra, general_infra, safety, stage="budget"):
    welfare_icons = mixed_icons([
        ("🏥", welfare, 5),
        ("👩‍⚕️", welfare, 4),
        ("🏘️", welfare, 3),
    ])

    education_icons = mixed_icons([
        ("🏫", education, 5),
        ("📚", education, 4),
        ("🎓", education, 3),
    ])

    energy_icons = mixed_icons([
        ("🔌", energy_infra, 5),
        ("🚗", energy_infra, 3),
        ("📡", energy_infra, 4),
    ])

    infra_icons = mixed_icons([
        ("🚌", general_infra, 4),
        ("🛣️", general_infra, 4),
        ("🌳", general_infra, 4),
    ])

    safety_icons = mixed_icons([
        ("👮", safety, 4),
        ("🚓", safety, 3),
        ("📹", safety, 3),
        ("🚒", safety, 2),
    ])

    st.markdown(
        f"""
        <div class="city-scene">
            <div class="city-sky">
                <div class="city-title">🏙️ NOVA시 정책 처치 적용 장면</div>
                <div class="city-weather">☀️ ☁️</div>
            </div>

            <div class="city-grid">
                <div class="district-zone">
                    <div class="district-name">복지 구역</div>
                    <div class="district-sub">복지 예산이 늘어나면 의료·돌봄 시설이 확충됩니다.</div>
                    <div class="icon-field">{welfare_icons}</div>
                </div>

                <div class="district-zone">
                    <div class="district-name">교육 구역</div>
                    <div class="district-sub">교육 예산이 늘어나면 학교·도서관·학습공간이 늘어납니다.</div>
                    <div class="icon-field">{education_icons}</div>
                </div>

                <div class="district-zone">
                    <div class="district-name">에너지 인프라 구역</div>
                    <div class="district-sub">에너지 인프라 예산은 충전소·스마트그리드로 표현됩니다.</div>
                    <div class="icon-field">{energy_icons}</div>
                </div>

                <div class="district-zone">
                    <div class="district-name">생활 인프라 구역</div>
                    <div class="district-sub">일반 인프라는 도로·버스·공원·생활SOC로 나타납니다.</div>
                    <div class="icon-field">{infra_icons}</div>
                </div>

                <div class="district-zone">
                    <div class="district-name">안전 구역</div>
                    <div class="district-sub">안전 예산은 경찰·CCTV·소방 체계 강화로 나타납니다.</div>
                    <div class="icon-field">{safety_icons}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_energy_scene(solar, hydrogen, ess, external):
    solar_icons = mixed_icons([
        ("☀️", solar, 4),
        ("🔆", solar, 4),
        ("🏠", solar, 4),
    ])

    hydrogen_icons = mixed_icons([
        ("💧", hydrogen, 4),
        ("⚗️", hydrogen, 4),
        ("🏭", hydrogen, 4),
    ])

    ess_icons = mixed_icons([
        ("🔋", ess, 7),
        ("⚡", ess, 5),
    ])

    external_icons = mixed_icons([
        ("🗼", external, 5),
        ("🔌", external, 4),
        ("🏭", external, 3),
    ])

    st.markdown(
        f"""
        <div class="energy-field">
            <div class="energy-zone">
                <div class="energy-title">태양광 설비</div>
                <div class="energy-desc">태양광 비중이 커질수록 지붕형 패널과 태양광 발전 시설이 늘어납니다.</div>
                <div class="energy-icons">{solar_icons}</div>
            </div>

            <div class="energy-zone">
                <div class="energy-title">수소연료전지</div>
                <div class="energy-desc">수소 비중이 커질수록 안정적인 도시 에너지 생산 시설이 늘어납니다.</div>
                <div class="energy-icons">{hydrogen_icons}</div>
            </div>

            <div class="energy-zone">
                <div class="energy-title">ESS 저장 시설</div>
                <div class="energy-desc">ESS 비중이 커질수록 남는 에너지를 저장하는 배터리 시설이 늘어납니다.</div>
                <div class="energy-icons">{ess_icons}</div>
            </div>

            <div class="energy-zone">
                <div class="energy-title">외부전력망</div>
                <div class="energy-desc">외부전력망 비중이 커질수록 도시 밖 전력망에 대한 의존이 커집니다.</div>
                <div class="energy-icons">{external_icons}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_effect_strip():
    st.markdown(
        """
        <div class="effect-strip">
            <div class="effect-item">
                <div class="effect-icon">🏥</div>
                <div class="effect-title">복지 처치</div>
                <div class="effect-desc">의료·돌봄·복지시설 확충</div>
            </div>
            <div class="effect-item">
                <div class="effect-icon">🏫</div>
                <div class="effect-title">교육 처치</div>
                <div class="effect-desc">학교·도서관·학습공간 증가</div>
            </div>
            <div class="effect-item">
                <div class="effect-icon">👮</div>
                <div class="effect-title">안전 처치</div>
                <div class="effect-desc">경찰·CCTV·소방 강화</div>
            </div>
            <div class="effect-item">
                <div class="effect-icon">🚌</div>
                <div class="effect-title">인프라 처치</div>
                <div class="effect-desc">도로·버스·공원 확충</div>
            </div>
            <div class="effect-item">
                <div class="effect-icon">⚡</div>
                <div class="effect-title">에너지 처치</div>
                <div class="effect-desc">충전소·발전·저장 설비 확대</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_dashboard_connection_card(
    dashboard_url,
    preset_choice,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external
):
    query = build_query_string(
        preset_choice,
        welfare,
        education,
        energy_infra,
        general_infra,
        safety,
        solar,
        hydrogen,
        ess,
        external
    )

    if dashboard_url:
        separator = "&" if "?" in dashboard_url else "?"
        linked_url = f"{dashboard_url}{separator}{query}"

        st.markdown(
            f"""
            <div class="dashboard-link-card">
                <div class="dashboard-link-title">📊 2차 결과물: 상세 대시보드로 이동</div>
                <div class="dashboard-link-desc">
                    이 화면은 정책 처치가 도시 장면에 적용되는 과정을 보여주는 1차 시뮬레이션입니다.
                    구체적인 만족도, 자립률, 구역별 차이, 시나리오 비교는 2차 대시보드에서 확인합니다.
                </div>
                <a class="dashboard-button" href="{linked_url}" target="_blank">
                    상세 대시보드 열기 →
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="dashboard-link-card">
                <div class="dashboard-link-title">📊 다음 단계: 2차 대시보드 확인</div>
                <div class="dashboard-link-desc">
                    이 시뮬레이션은 결과값을 자세히 분석하지 않고, 정책 처치가 도시 장면에 적용되는 과정만 보여줍니다.
                    발표에서는 이 장면형 시뮬레이션을 먼저 보여준 뒤, 기존 대시보드에서 최종 결과값을 설명하면 됩니다.
                    Streamlit Cloud에 배포한 대시보드 URL이 있다면 왼쪽 사이드바의
                    <b>2차 대시보드 URL</b>에 입력하세요.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==================================================
# 사이드바 입력
# ==================================================
with st.sidebar:
    st.markdown("## 🎛️ 정책 처치 설정")
    st.caption("이번 화면은 결과값 계산보다 정책 처치가 도시 장면에 적용되는 모습을 보여주는 시뮬레이션입니다.")

    preset_choice = st.selectbox("프리셋 시나리오", list(PRESETS.keys()))
    preset = PRESETS[preset_choice]

    preset_key = (
        preset_choice
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("⭐", "star")
    )

    def pv(key, default):
        return preset[key] if preset else default

    st.markdown("---")
    st.markdown("### 💰 예산 배분")

    welfare = st.slider("복지", 0, 100, pv("welfare", 20), 1, key=f"w_{preset_key}")
    education = st.slider("교육", 0, 100, pv("education", 18), 1, key=f"e_{preset_key}")
    energy_infra = st.slider("에너지 인프라", 0, 100, pv("energy_infra", 30), 1, key=f"ei_{preset_key}")
    general_infra = st.slider("일반 인프라", 0, 100, pv("general_infra", 22), 1, key=f"gi_{preset_key}")
    safety = st.slider("안전", 0, 100, pv("safety", 10), 1, key=f"s_{preset_key}")

    budget_total = welfare + education + energy_infra + general_infra + safety
    budget_ok = budget_total == 100

    if budget_ok:
        st.success(f"예산 합계: {budget_total}%")
    else:
        st.error(f"예산 합계: {budget_total}% · 정확히 100% 필요")

    st.markdown("---")
    st.markdown("### ⚡ 에너지 배분")

    solar = st.slider("태양광", 0, 100, pv("solar", 40), 1, key=f"sol_{preset_key}")
    hydrogen = st.slider("수소연료전지", 0, 100, pv("hydrogen", 35), 1, key=f"hyd_{preset_key}")
    ess = st.slider("ESS", 0, 100, pv("ess", 20), 1, key=f"ess_{preset_key}")
    external = st.slider("외부전력망", 0, 100, pv("external", 5), 1, key=f"ext_{preset_key}")

    energy_total = solar + hydrogen + ess + external
    energy_ok = energy_total == 100

    if energy_ok:
        st.success(f"에너지 합계: {energy_total}%")
    else:
        st.error(f"에너지 합계: {energy_total}% · 정확히 100% 필요")

    st.markdown("---")

    speed = st.slider("장면 전환 속도", 0.2, 2.0, 0.9, 0.1)

    default_dashboard_url = get_dashboard_url_from_secrets()
    dashboard_url = st.text_input(
        "2차 대시보드 URL",
        value=default_dashboard_url,
        placeholder="예: https://your-dashboard.streamlit.app"
    )
    st.caption("상세 결과 대시보드를 별도 앱으로 배포했다면 그 URL을 입력하세요.")

    play = st.button("🎬 정책 처치 장면 재생", type="primary", use_container_width=True)

# ==================================================
# 메인 화면
# ==================================================
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">NOVA Smart City Visual Simulation</div>
        <div class="title">정책 처치가 도시를 바꾸는 장면</div>
        <div class="subtitle">
            이 화면은 최종 점수와 분석표를 보여주는 대시보드가 아니라,
            예산과 에너지 배분이라는 처치가 도시 안에 어떤 시설과 장면으로 나타나는지를
            그림 중심으로 보여주는 시뮬레이션입니다.
        </div>
        <div class="pill-wrap">
            <div class="pill">복지 → 병원·돌봄센터</div>
            <div class="pill">교육 → 학교·도서관</div>
            <div class="pill">안전 → 경찰·CCTV</div>
            <div class="pill">인프라 → 도로·버스·공원</div>
            <div class="pill">에너지 → 태양광·수소·ESS</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if not budget_ok or not energy_ok:
    st.markdown(
        """
        <div class="notice-card">
            <b>시뮬레이션을 시작하려면 조건이 필요합니다.</b><br>
            예산 배분 합계와 에너지 배분 합계가 각각 정확히 100%가 되어야 합니다.
            왼쪽 슬라이더를 조정한 뒤 다시 실행해 주세요.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

if not play:
    st.markdown(
        """
        <div class="stage-card">
            <div class="stage-title">🎬 아직 정책 처치 장면이 재생되지 않았습니다</div>
            <div class="stage-desc">
                왼쪽에서 예산과 에너지 배분을 선택한 뒤 <b>정책 처치 장면 재생</b> 버튼을 누르면,
                각 예산 항목이 도시 시설로 바뀌는 과정을 그림으로 볼 수 있습니다.
                최종 수치 분석은 이 장면 이후 2차 대시보드에서 확인합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    show_process_map(1)
    show_effect_strip()
    show_city_scene(welfare, education, energy_infra, general_infra, safety)
    show_dashboard_connection_card(
        dashboard_url,
        preset_choice,
        welfare,
        education,
        energy_infra,
        general_infra,
        safety,
        solar,
        hydrogen,
        ess,
        external
    )
    st.stop()

# ==================================================
# 그림형 시뮬레이션 재생
# ==================================================
progress = st.progress(0)
status_area = st.empty()
content_area = st.empty()

# Scene 1
status_area.info("1장면: 정책 처치가 입력됩니다.")
progress.progress(15)
with content_area.container():
    show_process_map(1)

    st.markdown(
        """
        <div class="stage-card">
            <div class="stage-title">🎛️ 1장면. 정책 처치 입력</div>
            <div class="stage-desc">
                먼저 시민 만족도를 바꾸는 정책 처치를 입력합니다.
                여기서 처치는 예산과 에너지 비율입니다.
                이번 시뮬레이션에서는 이 값들이 최종 점수로 바로 계산되는 것이 아니라,
                도시 안의 시설 변화로 표현됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    show_budget_treatment_cards(welfare, education, energy_infra, general_infra, safety)

time.sleep(speed)

# Scene 2
status_area.info("2장면: 예산 처치가 도시 시설로 바뀝니다.")
progress.progress(35)
with content_area.container():
    show_process_map(2)

    st.markdown(
        """
        <div class="stage-card">
            <div class="stage-title">🏗️ 2장면. 예산이 도시 시설로 바뀌는 과정</div>
            <div class="stage-desc">
                복지 예산은 병원과 돌봄센터로, 교육 예산은 학교와 도서관으로,
                안전 예산은 경찰·CCTV·소방으로 표현됩니다.
                즉, 예산은 단순한 숫자가 아니라 시민이 실제로 보게 되는 도시 시설로 변환됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    show_effect_strip()
    show_city_scene(welfare, education, energy_infra, general_infra, safety)

time.sleep(speed)

# Scene 3
status_area.info("3장면: 에너지 처치가 도시 에너지 설비로 바뀝니다.")
progress.progress(55)
with content_area.container():
    show_process_map(3)

    st.markdown(
        """
        <div class="stage-card">
            <div class="stage-title">⚡ 3장면. 에너지 배분이 설비로 나타나는 과정</div>
            <div class="stage-desc">
                태양광 비중이 커지면 지붕형 태양광 패널이 늘어나고,
                수소연료전지 비중이 커지면 안정적인 발전 설비가 생깁니다.
                ESS는 에너지를 저장하는 배터리 시설로, 외부전력망은 도시 밖 전력망 의존으로 표현됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    show_energy_scene(solar, hydrogen, ess, external)

time.sleep(speed)

# Scene 4
status_area.info("4장면: 예산 시설과 에너지 설비가 결합된 스마트시티 장면이 완성됩니다.")
progress.progress(78)
with content_area.container():
    show_process_map(4)

    st.markdown(
        """
        <div class="stage-card">
            <div class="stage-title">🌆 4장면. 처치가 적용된 NOVA시</div>
            <div class="stage-desc">
                이제 예산 처치와 에너지 처치가 동시에 적용된 도시 장면을 봅니다.
                이 장면은 어떤 정책에 더 많은 자원을 배분했는지에 따라 도시의 모습이 달라진다는 점을 보여줍니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    show_city_scene(welfare, education, energy_infra, general_infra, safety)

    st.markdown('<div class="transition-arrow">＋</div>', unsafe_allow_html=True)

    show_energy_scene(solar, hydrogen, ess, external)

time.sleep(speed)

# Scene 5
status_area.success("5장면 완료: 그림형 처치 시뮬레이션이 끝났습니다.")
progress.progress(100)
with content_area.container():
    show_process_map(5)

    st.markdown(
        """
        <div class="final-scene-card">
            <div class="final-title">🎉 정책 처치 장면이 완성되었습니다</div>
            <div class="final-desc">
                지금까지의 화면은 예산과 에너지 배분이라는 정책 처치가 도시 안에서
                어떤 시설과 장면으로 나타나는지를 보여주는 1차 시뮬레이션입니다.
                구체적인 만족도 변화, 구역별 점수, 에너지 자립률, 시나리오 비교는
                이어서 2차 대시보드에서 확인하면 됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    show_effect_strip()
    show_city_scene(welfare, education, energy_infra, general_infra, safety)
    show_energy_scene(solar, hydrogen, ess, external)

show_dashboard_connection_card(
    dashboard_url,
    preset_choice,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external
)

st.markdown("### 발표 연결 문장 예시")
st.markdown(
    """
    이 장면형 시뮬레이션은 정책 처치가 도시 공간에 어떻게 나타나는지를 보여주는 단계입니다.  
    이제 같은 입력값을 바탕으로 2차 대시보드에서 실제 만족도, 에너지 자립률, 구역별 차이를 확인하겠습니다.
    """
)
