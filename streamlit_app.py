"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOVA시 스마트시티 영상형 시뮬레이션
simulation_story.py

기존 dashboard.py를 건드리지 않고,
예산·에너지 배분 처치가 결과로 이어지는 과정을
영상처럼 단계별로 보여주는 별도 Streamlit 앱입니다.

실행:
streamlit run simulation_story.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import time
import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(__file__))

from classes import (
    Worker, Student, Caregiver, Unemployed, Elder,
    SolarPanel, HydrogenCell, ESS, ExternalGrid,
    Resource, EnergyGrid, District, City,
    budget_to_fulfillment, energy_to_bonus,
    BudgetAllocationError, EnergyAllocationError
)

# ==================================================
# 페이지 설정
# ==================================================
st.set_page_config(
    page_title="NOVA시 시뮬레이션 과정",
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
        border-radius: 26px;
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
        max-width: 1000px;
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

    .story-card {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 22px;
        padding: 26px 28px;
        box-shadow: 0 10px 26px rgba(27,31,36,0.07);
        margin-bottom: 18px;
    }

    .story-title {
        font-size: 24px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 8px;
    }

    .story-desc {
        font-size: 15px;
        color: #57606a;
        line-height: 1.75;
    }

    .step-card {
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 14px;
    }

    .step-num {
        width: 40px;
        height: 40px;
        border-radius: 14px;
        background: #0969da;
        color: white;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 950;
        margin-right: 10px;
    }

    .step-head {
        font-size: 22px;
        font-weight: 950;
        color: #1f2328;
        display: flex;
        align-items: center;
        margin-bottom: 14px;
    }

    .step-body {
        font-size: 15px;
        color: #57606a;
        line-height: 1.75;
    }

    .metric-box {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 20px 22px;
        text-align: center;
        box-shadow: 0 8px 22px rgba(27,31,36,0.05);
    }

    .metric-label {
        font-size: 12px;
        color: #656d76;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 34px;
        font-weight: 950;
        color: #0969da;
        line-height: 1.1;
    }

    .metric-sub {
        font-size: 13px;
        color: #57606a;
        margin-top: 6px;
    }

    .arrow {
        text-align: center;
        font-size: 36px;
        color: #0969da;
        margin: 8px 0 18px;
        font-weight: 900;
    }

    .final-card {
        background: linear-gradient(135deg, #f0fff4 0%, #ddf4ff 100%);
        border: 1px solid #aceebb;
        border-radius: 24px;
        padding: 28px 30px;
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

    .small-note {
        color: #656d76;
        font-size: 13px;
        line-height: 1.65;
    }

    .warning-box {
        background: #fff8c5;
        border: 1px solid #f0d66b;
        border-radius: 16px;
        padding: 16px 18px;
        color: #1f2328;
        line-height: 1.65;
        font-size: 14px;
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

DISTRICT_KEYS = [
    "A구역(산업단지)",
    "B구역(대학가)",
    "C구역(복지타운)",
    "D구역(신도시)",
    "E구역(구도심)",
]

DISTRICT_LABELS = [
    "A구역 산업단지",
    "B구역 대학가",
    "C구역 복지타운",
    "D구역 신도시",
    "E구역 구도심",
]

# ==================================================
# 시뮬레이션 도시 생성
# ==================================================
@st.cache_resource
def get_city():
    worker = Worker()
    student = Student()
    caregiver = Caregiver()
    unemployed = Unemployed()
    elder = Elder()

    districts = [
        District(
            "A구역(산업단지)",
            {worker: 0.75, student: 0.05, caregiver: 0.08, unemployed: 0.07, elder: 0.05},
            0.45
        ),
        District(
            "B구역(대학가)",
            {worker: 0.10, student: 0.70, caregiver: 0.08, unemployed: 0.07, elder: 0.05},
            0.42
        ),
        District(
            "C구역(복지타운)",
            {worker: 0.05, student: 0.03, caregiver: 0.10, unemployed: 0.07, elder: 0.75},
            0.55
        ),
        District(
            "D구역(신도시)",
            {worker: 0.35, student: 0.25, caregiver: 0.20, unemployed: 0.10, elder: 0.10},
            0.40
        ),
        District(
            "E구역(구도심)",
            {worker: 0.30, student: 0.05, caregiver: 0.20, unemployed: 0.18, elder: 0.27},
            0.30
        ),
    ]

    return City("NOVA시", districts)

# ==================================================
# 계산 함수
# ==================================================
def expected_energy_self_rate(solar, hydrogen, ess, external):
    return (solar * 0.7 + hydrogen * 0.9 + ess * 0.6 + external * 0.0) / 100


def run_policy_simulation(
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
    try:
        resource = Resource(
            welfare=welfare / 100,
            education=education / 100,
            energy_infra=energy_infra / 100,
            general_infra=general_infra / 100,
            safety=safety / 100,
        )
    except BudgetAllocationError as e:
        return None, None, str(e)

    try:
        grid = EnergyGrid([
            SolarPanel(solar / 100),
            HydrogenCell(hydrogen / 100),
            ESS(ess / 100),
            ExternalGrid(external / 100),
        ])
    except EnergyAllocationError as e:
        return None, None, str(e)

    city = get_city()
    result = city.apply_policy(resource, grid)

    return result, resource, None


def score_color(score):
    if score < 50:
        return "#cf222e"
    if score < 60:
        return "#9a6700"
    if score < 75:
        return "#0969da"
    return "#1a7f37"


def make_budget_bar_chart(welfare, education, energy_infra, general_infra, safety):
    labels = ["복지", "교육", "에너지 인프라", "일반 인프라", "안전"]
    values = [welfare, education, energy_infra, general_infra, safety]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        text=[f"{v}%" for v in values],
        textposition="outside",
        marker_color=["#1a7f37", "#0969da", "#9a6700", "#8250df", "#cf222e"]
    ))

    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="입력된 예산 배분", font=dict(color="#1f2328", size=16)),
        xaxis=dict(tickfont=dict(color="#1f2328")),
        yaxis=dict(
            title=dict(text="비율(%)", font=dict(color="#1f2328")),
            tickfont=dict(color="#1f2328"),
            range=[0, 100],
            gridcolor="#d0d7de"
        ),
        showlegend=False,
    )
    return fig


def make_energy_bar_chart(solar, hydrogen, ess, external):
    labels = ["태양광", "수소연료전지", "ESS", "외부전력망"]
    values = [solar, hydrogen, ess, external]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        text=[f"{v}%" for v in values],
        textposition="outside",
        marker_color=["#fb8500", "#0969da", "#1f883d", "#656d76"]
    ))

    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="입력된 에너지 배분", font=dict(color="#1f2328", size=16)),
        xaxis=dict(tickfont=dict(color="#1f2328")),
        yaxis=dict(
            title=dict(text="비율(%)", font=dict(color="#1f2328")),
            tickfont=dict(color="#1f2328"),
            range=[0, 100],
            gridcolor="#d0d7de"
        ),
        showlegend=False,
    )
    return fig


def make_final_district_chart(result):
    scores = [result["districts"][k] for k in DISTRICT_KEYS]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=DISTRICT_LABELS,
        y=scores,
        text=[f"{v:.1f}점" for v in scores],
        textposition="outside",
        marker_color=[score_color(v) for v in scores]
    ))

    fig.add_hline(
        y=50,
        line_dash="dot",
        line_color="#cf222e",
        annotation_text="위험 기준 50점",
        annotation_font_color="#1f2328"
    )

    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="최종 구역별 시민 만족도", font=dict(color="#1f2328", size=16)),
        xaxis=dict(tickfont=dict(color="#1f2328")),
        yaxis=dict(
            title=dict(text="만족도 점수", font=dict(color="#1f2328")),
            tickfont=dict(color="#1f2328"),
            range=[30, 100],
            gridcolor="#d0d7de"
        ),
        showlegend=False,
    )
    return fig


def make_need_table(resource):
    need = resource.get_need_ratios()

    rows = []
    labels = {
        "health_safety": "건강·안전",
        "mobility": "모빌리티",
        "activities": "활동·문화",
        "opportunities": "기회·교육",
        "governance": "거버넌스",
    }

    for key, label in labels.items():
        ratio = need[key]
        score = budget_to_fulfillment(ratio)
        rows.append({
            "시민 니즈": label,
            "예산 반영 비율": f"{ratio * 100:.1f}%",
            "충족도 점수": f"{score:.1f}점"
        })

    return pd.DataFrame(rows)


def show_step_header(num, title, body):
    st.markdown(
        f"""
        <div class="step-card">
            <div class="step-head">
                <span class="step-num">{num}</span>
                {title}
            </div>
            <div class="step-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==================================================
# 사이드바 입력
# ==================================================
with st.sidebar:
    st.markdown("## 🎛️ 정책 처치 설정")
    st.caption("이 화면은 최종 대시보드가 아니라, 결과가 만들어지는 과정을 보여주는 영상형 시뮬레이터입니다.")

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

    speed = st.slider("재생 속도", 0.2, 2.0, 0.9, 0.1)
    play = st.button("🎬 시뮬레이션 과정 재생", type="primary", use_container_width=True)

# ==================================================
# 메인 화면
# ==================================================
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">NOVA Smart City Simulation Story</div>
        <div class="title">정책 처치가 시민 만족도로 이어지는 과정</div>
        <div class="subtitle">
            이 화면은 기존 대시보드를 보여주기 전, 예산 배분과 에너지 배분이라는 처치가
            시민 니즈, 에너지 자립률, 절감액 환원, 구역별 만족도라는 결과로 이어지는 흐름을
            단계별로 보여주는 영상형 시뮬레이터입니다.
        </div>
        <div class="pill-wrap">
            <div class="pill">1. 예산 배분 입력</div>
            <div class="pill">2. 시민 니즈 변환</div>
            <div class="pill">3. 에너지 자립률 계산</div>
            <div class="pill">4. 선순환 효과</div>
            <div class="pill">5. 최종 만족도 산출</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if not budget_ok or not energy_ok:
    st.markdown(
        """
        <div class="warning-box">
            <b>시뮬레이션을 시작하려면 조건이 필요합니다.</b><br>
            예산 배분 합계와 에너지 배분 합계가 각각 정확히 100%가 되어야 합니다.
            왼쪽 슬라이더를 조정한 뒤 다시 실행해 주세요.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

result, resource, err = run_policy_simulation(
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

if err:
    st.error(err)
    st.stop()

if not play:
    st.markdown(
        """
        <div class="story-card">
            <div class="story-title">🎬 아직 시뮬레이션이 재생되지 않았습니다</div>
            <div class="story-desc">
                왼쪽 사이드바에서 정책 처치를 설정한 뒤
                <b>시뮬레이션 과정 재생</b> 버튼을 누르면,
                예산과 에너지 배분이 최종 시민 만족도로 이어지는 과정을 단계별로 볼 수 있습니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            make_budget_bar_chart(welfare, education, energy_infra, general_infra, safety),
            use_container_width=True,
            config={"displayModeBar": False}
        )
    with col2:
        st.plotly_chart(
            make_energy_bar_chart(solar, hydrogen, ess, external),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    st.stop()

# ==================================================
# 영상형 시뮬레이션 재생
# ==================================================
progress = st.progress(0)
status_area = st.empty()
content_area = st.empty()

# Step 1
status_area.info("1단계 실행 중: 예산 배분 처치를 적용합니다.")
progress.progress(10)
with content_area.container():
    show_step_header(
        1,
        "예산 배분 처치 적용",
        "사용자가 설정한 예산 배분은 도시 정책의 출발점입니다. 이 단계에서는 복지, 교육, 에너지 인프라, 일반 인프라, 안전에 투입되는 자원의 비중을 확인합니다."
    )
    st.plotly_chart(
        make_budget_bar_chart(welfare, education, energy_infra, general_infra, safety),
        use_container_width=True,
        config={"displayModeBar": False}
    )
time.sleep(speed)

# Step 2
status_area.info("2단계 실행 중: 예산 배분을 시민 니즈 충족도로 변환합니다.")
progress.progress(30)
with content_area.container():
    show_step_header(
        2,
        "예산 → 시민 니즈 충족도 변환",
        "예산은 단순 금액이 아니라 시민이 체감하는 건강·안전, 모빌리티, 활동·문화, 기회·교육, 거버넌스 니즈로 변환됩니다."
    )
    st.dataframe(make_need_table(resource), use_container_width=True, hide_index=True)
time.sleep(speed)

# Step 3
predicted_rate = expected_energy_self_rate(solar, hydrogen, ess, external)
status_area.info("3단계 실행 중: 에너지 배분으로 에너지 자립률을 계산합니다.")
progress.progress(50)
with content_area.container():
    show_step_header(
        3,
        "에너지 배분 → 에너지 자립률 계산",
        "태양광, 수소연료전지, ESS는 도시 자체의 에너지 자립률에 기여합니다. 외부전력망은 전력 공급에는 도움을 주지만 자체 생산이 아니므로 자립률에는 기여하지 않습니다."
    )

    col1, col2 = st.columns([1.1, 1])
    with col1:
        st.plotly_chart(
            make_energy_bar_chart(solar, hydrogen, ess, external),
            use_container_width=True,
            config={"displayModeBar": False}
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">예상 에너지 자립률</div>
                <div class="metric-value">{predicted_rate * 100:.1f}%</div>
                <div class="metric-sub">
                    태양광×0.7 + 수소×0.9 + ESS×0.6 + 외부전력망×0.0
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
time.sleep(speed)

# Step 4
status_area.info("4단계 실행 중: 에너지 자립률에 따른 선순환 효과를 계산합니다.")
progress.progress(70)
with content_area.container():
    show_step_header(
        4,
        "에너지 자립률 → 절감액 환원 효과",
        "에너지 자립률이 높아지면 외부 전력 의존도가 줄고, 그 절감 효과 일부가 복지·교육 예산으로 환원됩니다. 이 구조가 에너지-예산 선순환입니다."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">에너지 자립률</div>
                <div class="metric-value">{result['independence_rate'] * 100:.1f}%</div>
                <div class="metric-sub">에너지 배분 결과</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">절감액 환원</div>
                <div class="metric-value">{result['savings'] * 100:.2f}%</div>
                <div class="metric-sub">복지·교육 재배분 효과</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        bonus = energy_to_bonus(result["independence_rate"])
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">만족도 보정</div>
                <div class="metric-value">{bonus:+.1f}점</div>
                <div class="metric-sub">에너지 안정성 보정값</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="arrow">↓</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="story-card">
            <div class="story-title">🔁 선순환 구조</div>
            <div class="story-desc">
                에너지 자립률 상승 → 외부 전력 의존 감소 → 비용 절감 → 복지·교육 예산 환원 → 시민 만족도 상승
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
time.sleep(speed)

# Step 5
status_area.success("5단계 완료: 구역별 시민 만족도와 도시 평균 만족도가 산출되었습니다.")
progress.progress(100)
with content_area.container():
    show_step_header(
        5,
        "최종 결과 산출",
        "마지막으로 각 구역의 시민 구성과 니즈 차이를 반영하여 구역별 만족도와 도시 평균 만족도를 계산합니다."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">도시 평균 만족도</div>
                <div class="metric-value">{result['city_average']:.1f}점</div>
                <div class="metric-sub">NOVA시 전체 평균</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        warnings = result["warnings"]
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">위험 구역 수</div>
                <div class="metric-value">{len(warnings)}개</div>
                <div class="metric-sub">만족도 50점 미만</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">프리셋</div>
                <div class="metric-value" style="font-size:24px;">{preset_choice}</div>
                <div class="metric-sub">현재 적용된 정책 조합</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.plotly_chart(
        make_final_district_chart(result),
        use_container_width=True,
        config={"displayModeBar": False}
    )

st.markdown(
    """
    <div class="final-card">
        <div class="final-title">🎉 시뮬레이션 과정이 완료되었습니다</div>
        <div class="final-desc">
            지금 화면은 정책 처치가 결과로 이어지는 과정을 설명하기 위한 1차 시뮬레이션입니다.
            발표에서는 이 과정을 먼저 보여준 뒤, 기존에 만들어둔 대시보드를 2차 결과물로 제시하면 됩니다.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("### 다음 단계")
st.markdown(
    """
    이제 기존에 만든 `dashboard.py`를 실행해서,  
    같은 입력값에 대한 **상세 대시보드 결과**를 보여주면 됩니다.

    ```bash
    streamlit run dashboard.py
    ```
    """
)
