"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOVA시 게임형 스마트시티 정책 처치 시뮬레이션
simulation_story.py

역할:
- 기존 dashboard.py는 건드리지 않음
- 1차 결과물: 예산·에너지 배분 처치가 A~E구역의 도시 구조를 바꾸는 장면을 게임처럼 표현
- 2차 결과물: 기존 dashboard.py에서 만족도, 자립률, 시나리오 비교를 상세 분석

실행:
streamlit run simulation_story.py

필요 requirements.txt:
streamlit
pandas
plotly
numpy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import html as html_lib
import urllib.parse
from itertools import cycle

import streamlit as st
import streamlit.components.v1 as components


# ==================================================
# 기존 dashboard.py / classes.py 기반 import
# ==================================================
sys.path.insert(0, os.path.dirname(__file__))

try:
    from classes import (
        Worker, Student, Caregiver, Unemployed, Elder,
        SolarPanel, HydrogenCell, ESS, ExternalGrid,
        Resource, EnergyGrid, District, City,
        budget_to_fulfillment, energy_to_bonus,
        BudgetAllocationError, LowSatisfactionWarning, EnergyAllocationError
    )
    HAS_CLASSES = True
except Exception as import_error:
    HAS_CLASSES = False
    IMPORT_ERROR_MESSAGE = str(import_error)


# ==================================================
# Streamlit 페이지 설정
# ==================================================
st.set_page_config(
    page_title="NOVA시 게임형 정책 시뮬레이션",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# 기존 dashboard.py와 동일한 프리셋
# ==================================================
PRESETS = {
    "직접 입력": None,

    "초기 상태 (인프라 편중)": dict(
        welfare=15,
        education=15,
        energy_infra=10,
        general_infra=45,
        safety=15,
        solar=10,
        hydrogen=5,
        ess=5,
        external=80,
    ),

    "복지 집중": dict(
        welfare=40,
        education=15,
        energy_infra=15,
        general_infra=20,
        safety=10,
        solar=25,
        hydrogen=15,
        ess=15,
        external=45,
    ),

    "에너지 자립 집중": dict(
        welfare=12,
        education=10,
        energy_infra=45,
        general_infra=23,
        safety=10,
        solar=45,
        hydrogen=30,
        ess=20,
        external=5,
    ),

    "균형 배분": dict(
        welfare=22,
        education=20,
        energy_infra=20,
        general_infra=23,
        safety=15,
        solar=35,
        hydrogen=25,
        ess=20,
        external=20,
    ),

    "선순환 최적 ⭐": dict(
        welfare=20,
        education=18,
        energy_infra=30,
        general_infra=22,
        safety=10,
        solar=40,
        hydrogen=35,
        ess=20,
        external=5,
    ),
}


DISTRICT_KEYS = [
    "A구역(산업단지)",
    "B구역(대학가)",
    "C구역(복지타운)",
    "D구역(신도시)",
    "E구역(구도심)",
]


DISTRICT_INFO = {
    "A구역(산업단지)": {
        "short": "A구역",
        "name": "산업단지",
        "main_icon": "🏭",
        "desc": "근로자 중심 · 이동성·일자리 민감",
        "theme": "industry",
        "base_icons": ["🏭", "🏢", "🏗️"],
        "weights": {
            "welfare": 0.45,
            "education": 0.35,
            "energy_infra": 1.25,
            "general_infra": 1.35,
            "safety": 0.85,
        },
    },

    "B구역(대학가)": {
        "short": "B구역",
        "name": "대학가",
        "main_icon": "🎓",
        "desc": "학생 중심 · 교육·문화 민감",
        "theme": "campus",
        "base_icons": ["🏫", "🏛️", "🏠"],
        "weights": {
            "welfare": 0.35,
            "education": 1.60,
            "energy_infra": 0.55,
            "general_infra": 0.90,
            "safety": 0.65,
        },
    },

    "C구역(복지타운)": {
        "short": "C구역",
        "name": "복지타운",
        "main_icon": "🏥",
        "desc": "노인·취약계층 중심 · 복지·안전 민감",
        "theme": "welfare",
        "base_icons": ["🏥", "🏘️", "🏠"],
        "weights": {
            "welfare": 1.65,
            "education": 0.35,
            "energy_infra": 0.55,
            "general_infra": 0.70,
            "safety": 1.10,
        },
    },

    "D구역(신도시)": {
        "short": "D구역",
        "name": "신도시",
        "main_icon": "🏙️",
        "desc": "혼합형 시민 구성 · 균형 정책 반응",
        "theme": "newtown",
        "base_icons": ["🏙️", "🏢", "🏬"],
        "weights": {
            "welfare": 0.90,
            "education": 0.90,
            "energy_infra": 1.05,
            "general_infra": 1.05,
            "safety": 0.90,
        },
    },

    "E구역(구도심)": {
        "short": "E구역",
        "name": "구도심",
        "main_icon": "🏚️",
        "desc": "노후 인프라 · 복지·안전·생활SOC 민감",
        "theme": "oldtown",
        "base_icons": ["🏚️", "🏠", "🏘️"],
        "weights": {
            "welfare": 1.15,
            "education": 0.55,
            "energy_infra": 0.60,
            "general_infra": 1.10,
            "safety": 1.25,
        },
    },
}


# ==================================================
# 기존 dashboard.py와 같은 도시 초기화
# ==================================================
@st.cache_resource
def get_city():
    if not HAS_CLASSES:
        return None

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


def run_simulation_from_classes(
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external,
):
    """
    dashboard.py의 run_simulation()과 같은 방식으로 classes.py 모델을 실행한다.
    실패하면 None, error_message를 반환한다.
    """
    if not HAS_CLASSES:
        return None, "classes.py를 불러오지 못했습니다."

    try:
        resource = Resource(
            welfare=welfare / 100,
            education=education / 100,
            energy_infra=energy_infra / 100,
            general_infra=general_infra / 100,
            safety=safety / 100,
        )
    except BudgetAllocationError as e:
        return None, str(e)

    try:
        grid = EnergyGrid([
            SolarPanel(solar / 100),
            HydrogenCell(hydrogen / 100),
            ESS(ess / 100),
            ExternalGrid(external / 100),
        ])
    except EnergyAllocationError as e:
        return None, str(e)

    try:
        city = get_city()
        result = city.apply_policy(resource, grid)
        return result, None
    except Exception as e:
        return None, str(e)


def run_model_or_fallback(
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external,
):
    """
    우선 classes.py 기반 실제 모델을 사용한다.
    만약 Streamlit Cloud에서 import 문제나 예상치 못한 오류가 발생해도
    게임형 화면이 죽지 않도록 화면용 fallback 계산을 사용한다.
    """
    result, err = run_simulation_from_classes(
        welfare,
        education,
        energy_infra,
        general_infra,
        safety,
        solar,
        hydrogen,
        ess,
        external,
    )

    if result is not None:
        scores = {
            key: float(result["districts"][key])
            for key in DISTRICT_KEYS
        }

        return {
            "scores": scores,
            "average": float(result["city_average"]),
            "independence": float(result["independence_rate"]),
            "savings": float(result["savings"]),
            "warnings": result.get("warnings", []),
            "source": "classes.py OOP 모델",
            "raw_result": result,
        }

    # fallback: 화면이 깨지지 않도록 보조 계산
    energy_rate = expected_energy_self_rate(solar, hydrogen, ess, external)
    energy_bonus = (energy_rate - 0.4) * 18

    scores = {
        "A구역(산업단지)": (
            42
            + general_infra * 0.30
            + energy_infra * 0.18
            + safety * 0.15
            + education * 0.08
            + welfare * 0.05
            + energy_bonus
        ),
        "B구역(대학가)": (
            40
            + education * 0.33
            + general_infra * 0.14
            + safety * 0.08
            + energy_infra * 0.08
            + welfare * 0.05
            + energy_bonus
        ),
        "C구역(복지타운)": (
            38
            + welfare * 0.38
            + safety * 0.18
            + general_infra * 0.08
            + education * 0.05
            + energy_infra * 0.05
            + energy_bonus
        ),
        "D구역(신도시)": (
            43
            + welfare * 0.16
            + education * 0.16
            + energy_infra * 0.16
            + general_infra * 0.18
            + safety * 0.14
            + energy_bonus
        ),
        "E구역(구도심)": (
            36
            + welfare * 0.22
            + safety * 0.22
            + general_infra * 0.20
            + education * 0.06
            + energy_infra * 0.07
            + energy_bonus
        ),
    }

    scores = {
        key: max(30, min(95, value))
        for key, value in scores.items()
    }

    average = sum(scores.values()) / len(scores)
    warnings = [key for key, value in scores.items() if value < 50]

    return {
        "scores": scores,
        "average": average,
        "independence": energy_rate,
        "savings": max(0, energy_rate - 0.4) * 0.05,
        "warnings": warnings,
        "source": f"화면용 보조 계산 · 실제 모델 오류: {err}",
        "raw_result": None,
    }


# ==================================================
# 화면 생성 유틸
# ==================================================
def score_face(score):
    if score < 50:
        return "😟"
    if score < 60:
        return "😐"
    if score < 75:
        return "🙂"
    return "😄"


def score_mood(score):
    if score < 50:
        return "불안"
    if score < 60:
        return "보통"
    if score < 75:
        return "만족"
    return "행복"


def score_color(score):
    if score < 50:
        return "#cf222e"
    if score < 60:
        return "#9a6700"
    if score < 75:
        return "#0969da"
    return "#1a7f37"


def clamp(value, low, high):
    return max(low, min(high, value))


def icon_count(value, weight=1.0, max_icons=8, divisor=10):
    """
    예산 비율을 건물 개수로 변환한다.
    값이 높을수록 해당 구역에 더 많은 시설이 생긴다.
    """
    count = round((value * weight) / divisor)
    return clamp(count, 0, max_icons)


def make_icon_spans(symbols, count, base_delay=1.0, cls="facility"):
    if count <= 0:
        return ""

    symbol_cycle = cycle(symbols)
    result = []

    for i in range(count):
        symbol = next(symbol_cycle)
        delay = base_delay + i * 0.11
        result.append(
            f'<span class="{cls}" style="animation-delay:{delay:.2f}s">{symbol}</span>'
        )

    return "".join(result)


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
    external,
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


def make_dashboard_link(
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
    external,
):
    if not dashboard_url:
        return ""

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
        external,
    )

    separator = "&" if "?" in dashboard_url else "?"
    linked = f"{dashboard_url}{separator}{query}"
    escaped = html_lib.escape(linked, quote=True)

    return f"""
    <a class="dashboard-button" href="{escaped}" target="_blank">
        📊 2차 상세 대시보드 열기
    </a>
    """


def make_people(score, district_index):
    face = score_face(score)
    people = []

    for i in range(7):
        delay = 9.0 + district_index * 0.25 + i * 0.12
        top = 70 + (i % 2) * 14
        left = 7 + i * 12

        people.append(
            f"""
            <span class="citizen"
                  style="left:{left}%; top:{top}%; animation-delay:{delay:.2f}s">
                {face}
            </span>
            """
        )

    return "".join(people)


def make_vehicle_icons(general_infra, safety, district_index):
    buses = icon_count(general_infra, 0.80, 3, divisor=18)
    police = icon_count(safety, 0.75, 3, divisor=18)

    items = []

    for i in range(buses):
        delay = 6.2 + district_index * 0.2 + i * 0.35
        items.append(
            f'<span class="vehicle bus" style="animation-delay:{delay:.2f}s">🚌</span>'
        )

    for i in range(police):
        delay = 6.9 + district_index * 0.2 + i * 0.35
        items.append(
            f'<span class="vehicle police" style="animation-delay:{delay:.2f}s">🚓</span>'
        )

    return "".join(items)


def district_facilities(
    district_key,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    district_index,
):
    info = DISTRICT_INFO[district_key]
    weights = info["weights"]

    base = make_icon_spans(
        info["base_icons"],
        3,
        0.6 + district_index * 0.12,
        cls="facility base-building",
    )

    welfare_icons = make_icon_spans(
        ["🏥", "👩‍⚕️", "🏘️", "🤝"],
        icon_count(welfare, weights["welfare"], 8, divisor=10),
        1.5 + district_index * 0.12,
    )

    education_icons = make_icon_spans(
        ["🏫", "📚", "🎓", "🏛️"],
        icon_count(education, weights["education"], 8, divisor=10),
        2.4 + district_index * 0.12,
    )

    energy_icons = make_icon_spans(
        ["🔌", "📡", "🚗", "💡"],
        icon_count(energy_infra, weights["energy_infra"], 8, divisor=10),
        3.3 + district_index * 0.12,
    )

    infra_icons = make_icon_spans(
        ["🌳", "🛣️", "🚌", "🚏", "🏞️"],
        icon_count(general_infra, weights["general_infra"], 8, divisor=10),
        4.2 + district_index * 0.12,
    )

    safety_icons = make_icon_spans(
        ["👮", "📹", "🚒", "🚓", "🛡️"],
        icon_count(safety, weights["safety"], 8, divisor=10),
        5.1 + district_index * 0.12,
    )

    return base + welfare_icons + education_icons + energy_icons + infra_icons + safety_icons


def make_district_card(
    district_key,
    score,
    district_index,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
):
    info = DISTRICT_INFO[district_key]
    color = score_color(score)
    face = score_face(score)
    mood = score_mood(score)

    facilities = district_facilities(
        district_key,
        welfare,
        education,
        energy_infra,
        general_infra,
        safety,
        district_index,
    )

    citizens = make_people(score, district_index)
    vehicles = make_vehicle_icons(general_infra, safety, district_index)

    return f"""
    <div class="district-card district-{district_index + 1}">
        <div class="district-banner">
            <div class="district-main-icon">{info["main_icon"]}</div>
            <div>
                <div class="district-title">{info["short"]} · {info["name"]}</div>
                <div class="district-desc">{info["desc"]}</div>
            </div>
        </div>

        <div class="district-map">
            <div class="green-patch patch-a"></div>
            <div class="green-patch patch-b"></div>
            <div class="water-tile"></div>
            <div class="district-road road-a"></div>
            <div class="district-road road-b"></div>

            <div class="facility-layer">
                {facilities}
            </div>

            <div class="vehicle-layer">
                {vehicles}
            </div>

            <div class="citizen-layer">
                {citizens}
            </div>
        </div>

        <div class="district-status">
            <div class="mood-face">{face}</div>
            <div class="mood-detail">
                <div class="mood-label">시민 반응 · {mood}</div>
                <div class="mood-bar">
                    <div class="mood-fill"
                         style="--score-width:{score:.1f}%; --score-color:{color};">
                    </div>
                </div>
            </div>
            <div class="mood-score" style="color:{color};">{score:.1f}</div>
        </div>
    </div>
    """


def make_energy_zone(solar, hydrogen, ess, external):
    solar_icons = make_icon_spans(
        ["☀️", "🔆", "🏠"],
        icon_count(solar, 1.15, 13, divisor=9),
        6.0,
        cls="energy-icon"
    )

    hydrogen_icons = make_icon_spans(
        ["💧", "⚗️", "🏭"],
        icon_count(hydrogen, 1.15, 13, divisor=9),
        6.4,
        cls="energy-icon"
    )

    ess_icons = make_icon_spans(
        ["🔋", "⚡"],
        icon_count(ess, 1.20, 13, divisor=9),
        6.8,
        cls="energy-icon"
    )

    external_icons = make_icon_spans(
        ["🗼", "🔌"],
        icon_count(external, 1.05, 13, divisor=9),
        7.2,
        cls="energy-icon"
    )

    return f"""
    <section class="energy-board">
        <div class="section-heading">
            <div>
                <div class="section-title">⚡ 도시 외곽 에너지 설비</div>
                <div class="section-subtitle">
                    에너지 배분값이 높을수록 해당 발전·저장 설비가 더 많이 생깁니다.
                </div>
            </div>
        </div>

        <div class="energy-grid">
            <div class="energy-card solar">
                <div class="energy-card-title">태양광 단지</div>
                <div class="energy-card-desc">태양광 {solar}%</div>
                <div class="energy-icon-field">{solar_icons}</div>
            </div>

            <div class="energy-card hydrogen">
                <div class="energy-card-title">수소연료전지</div>
                <div class="energy-card-desc">수소 {hydrogen}%</div>
                <div class="energy-icon-field">{hydrogen_icons}</div>
            </div>

            <div class="energy-card ess">
                <div class="energy-card-title">ESS 저장소</div>
                <div class="energy-card-desc">ESS {ess}%</div>
                <div class="energy-icon-field">{ess_icons}</div>
            </div>

            <div class="energy-card external">
                <div class="energy-card-title">외부전력망</div>
                <div class="energy-card-desc">외부전력망 {external}%</div>
                <div class="energy-icon-field">{external_icons}</div>
            </div>
        </div>
    </section>
    """


def make_game_html(
    preset_choice,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external,
    model_result,
    dashboard_url,
):
    scores = model_result["scores"]
    avg = model_result["average"]
    independence = model_result["independence"]
    savings = model_result["savings"]
    warnings = model_result["warnings"]
    model_source = model_result["source"]

    district_html = ""

    for idx, key in enumerate(DISTRICT_KEYS):
        district_html += make_district_card(
            key,
            scores[key],
            idx,
            welfare,
            education,
            energy_infra,
            general_infra,
            safety,
        )

    warning_text = f"{len(warnings)}개 구역 주의" if warnings else "위험 구역 없음"
    warning_color = "#cf222e" if warnings else "#1a7f37"

    dashboard_button = make_dashboard_link(
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
        external,
    )

    if not dashboard_button:
        dashboard_button = """
        <div class="dashboard-empty">
            왼쪽 사이드바의 2차 대시보드 URL에 기존 대시보드 주소를 입력하면 이동 버튼이 생성됩니다.
        </div>
        """

    css = """
    <style>
    :root {
        --ink: #1f2328;
        --muted: #57606a;
        --line: #d0d7de;
        --blue: #0969da;
        --green: #1a7f37;
        --red: #cf222e;
        --yellow: #9a6700;
        --purple: #8250df;
        --sky: #ddf4ff;
        --grass: #b7e4a8;
        --grass-dark: #6ab04c;
        --road: #737b85;
        --water: #74c0fc;
    }

    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        background: #ffffff;
        color: var(--ink);
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .game-root {
        width: 100%;
        padding: 4px 6px 44px;
    }

    .game-top {
        position: relative;
        overflow: hidden;
        border-radius: 30px;
        min-height: 245px;
        padding: 30px 34px;
        color: white;
        background:
            radial-gradient(circle at 12% 25%, rgba(255,255,255,0.20), transparent 18%),
            radial-gradient(circle at 88% 20%, rgba(255,255,255,0.16), transparent 20%),
            linear-gradient(135deg, #a3652f 0%, #cd7c35 42%, #e3a04d 100%);
        box-shadow: 0 18px 42px rgba(163,101,47,0.22);
        margin-bottom: 18px;
    }

    .wood-plank {
        position: absolute;
        inset: 0;
        background:
            repeating-linear-gradient(
                165deg,
                rgba(255,255,255,0.06) 0 8px,
                rgba(0,0,0,0.04) 8px 18px
            );
        pointer-events: none;
    }

    .top-content {
        position: relative;
        z-index: 2;
        display: grid;
        grid-template-columns: 1.45fr 1fr;
        gap: 20px;
        align-items: center;
    }

    .game-eyebrow {
        font-size: 13px;
        font-weight: 950;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        opacity: 0.90;
        margin-bottom: 8px;
    }

    .game-title {
        font-size: 42px;
        font-weight: 950;
        line-height: 1.16;
        text-shadow: 0 3px 0 rgba(0,0,0,0.15);
        margin-bottom: 10px;
    }

    .game-desc {
        max-width: 900px;
        font-size: 16px;
        line-height: 1.7;
        opacity: 0.96;
    }

    .resource-panel {
        background: rgba(255,255,255,0.18);
        border: 1px solid rgba(255,255,255,0.28);
        border-radius: 24px;
        padding: 18px;
        backdrop-filter: blur(6px);
    }

    .resource-row {
        display: grid;
        grid-template-columns: 42px 1fr 82px;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.18);
    }

    .resource-row:last-child {
        border-bottom: none;
    }

    .resource-icon {
        width: 38px;
        height: 38px;
        border-radius: 14px;
        background: rgba(255,255,255,0.22);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
    }

    .resource-name {
        font-size: 13px;
        font-weight: 900;
    }

    .resource-value {
        text-align: right;
        font-size: 18px;
        font-weight: 950;
    }

    .hud-grid {
        display: grid;
        grid-template-columns: 1.2fr 1fr 1fr 1fr;
        gap: 14px;
        margin-bottom: 18px;
    }

    .hud-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 18px 20px;
        min-height: 118px;
        box-shadow: 0 10px 26px rgba(27,31,36,0.07);
        animation: uiPop 0.7s ease both;
    }

    .hud-card:nth-child(1) { animation-delay: 0.1s; }
    .hud-card:nth-child(2) { animation-delay: 0.2s; }
    .hud-card:nth-child(3) { animation-delay: 0.3s; }
    .hud-card:nth-child(4) { animation-delay: 0.4s; }

    @keyframes uiPop {
        from { transform: translateY(16px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    .hud-label {
        font-size: 12px;
        font-weight: 950;
        color: #656d76;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }

    .hud-value {
        font-size: 30px;
        font-weight: 950;
        color: var(--blue);
        line-height: 1.05;
    }

    .hud-sub {
        font-size: 13px;
        color: var(--muted);
        line-height: 1.5;
        margin-top: 8px;
    }

    .quest-panel {
        background: #fff8c5;
        border: 1px solid #f0d66b;
        border-radius: 22px;
        padding: 16px 18px;
        margin-bottom: 18px;
        display: grid;
        grid-template-columns: 54px 1fr;
        gap: 12px;
        align-items: center;
        box-shadow: 0 10px 24px rgba(210,153,34,0.10);
    }

    .quest-icon {
        width: 52px;
        height: 52px;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid #f0d66b;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
    }

    .quest-title {
        font-size: 17px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 4px;
    }

    .quest-desc {
        font-size: 14px;
        color: var(--muted);
        line-height: 1.6;
    }

    .timeline {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 18px;
    }

    .timeline-step {
        background: #f6f8fa;
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 14px 12px;
        text-align: center;
        min-height: 126px;
        animation: stepFocus 11s ease both;
    }

    .timeline-step:nth-child(1) { animation-delay: 0.0s; }
    .timeline-step:nth-child(2) { animation-delay: 2.0s; }
    .timeline-step:nth-child(3) { animation-delay: 4.0s; }
    .timeline-step:nth-child(4) { animation-delay: 6.0s; }
    .timeline-step:nth-child(5) { animation-delay: 8.0s; }

    @keyframes stepFocus {
        0%, 16% {
            background: linear-gradient(135deg, #ddf4ff 0%, #ffffff 100%);
            border-color: var(--blue);
            box-shadow: 0 10px 24px rgba(9,105,218,0.15);
            transform: translateY(-3px);
        }
        24%, 100% {
            background: #f6f8fa;
            border-color: var(--line);
            box-shadow: none;
            transform: translateY(0);
        }
    }

    .timeline-icon {
        font-size: 30px;
        margin-bottom: 8px;
    }

    .timeline-title {
        font-size: 14px;
        font-weight: 950;
        margin-bottom: 5px;
    }

    .timeline-desc {
        font-size: 12px;
        color: var(--muted);
        line-height: 1.45;
    }

    .section-heading {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 16px;
        margin-bottom: 14px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 5px;
    }

    .section-subtitle {
        font-size: 14px;
        color: var(--muted);
        line-height: 1.6;
    }

    .city-board {
        position: relative;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 32px;
        padding: 22px;
        background:
            linear-gradient(180deg, #ddf4ff 0%, #f8fcff 32%, #eaf8e1 100%);
        box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.8),
            0 14px 34px rgba(27,31,36,0.08);
        margin-bottom: 22px;
    }

    .city-board::before {
        content: "☀️";
        position: absolute;
        top: 20px;
        right: 28px;
        font-size: 58px;
        animation: sunSpin 12s linear infinite;
        z-index: 1;
    }

    @keyframes sunSpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .cloud {
        position: absolute;
        font-size: 42px;
        opacity: 0.65;
        z-index: 1;
        animation: cloudMove 10s ease-in-out infinite alternate;
    }

    .cloud.one { top: 58px; left: 5%; }
    .cloud.two { top: 34px; left: 42%; animation-delay: 1.5s; }

    @keyframes cloudMove {
        from { transform: translateX(0); }
        to { transform: translateX(42px); }
    }

    .map-container {
        position: relative;
        z-index: 2;
    }

    .city-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
    }

    .district-card {
        position: relative;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.95), rgba(255,255,255,0.88));
        border: 1px solid var(--line);
        border-radius: 26px;
        padding: 15px 13px;
        min-height: 430px;
        overflow: hidden;
        box-shadow: 0 10px 24px rgba(27,31,36,0.08);
        animation: districtAppear 0.8s ease both;
    }

    .district-1 { animation-delay: 0.2s; }
    .district-2 { animation-delay: 0.35s; }
    .district-3 { animation-delay: 0.50s; }
    .district-4 { animation-delay: 0.65s; }
    .district-5 { animation-delay: 0.80s; }

    @keyframes districtAppear {
        from { transform: translateY(18px) scale(0.98); opacity: 0; }
        to { transform: translateY(0) scale(1); opacity: 1; }
    }

    .district-banner {
        display: grid;
        grid-template-columns: 48px 1fr;
        gap: 10px;
        align-items: center;
        margin-bottom: 12px;
    }

    .district-main-icon {
        width: 48px;
        height: 48px;
        border-radius: 18px;
        background: #f6f8fa;
        border: 1px solid var(--line);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 27px;
    }

    .district-title {
        font-size: 15px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 3px;
    }

    .district-desc {
        font-size: 11px;
        color: var(--muted);
        line-height: 1.35;
    }

    .district-map {
        position: relative;
        height: 270px;
        border-radius: 22px;
        overflow: hidden;
        border: 1px dashed #b9c0c9;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.55), rgba(255,255,255,0.20)),
            repeating-linear-gradient(45deg, #b7e4a8 0 18px, #a8db98 18px 36px);
        margin-bottom: 12px;
    }

    .district-map::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 20% 22%, rgba(255,255,255,0.35) 0 20px, transparent 21px),
            radial-gradient(circle at 78% 70%, rgba(255,255,255,0.30) 0 24px, transparent 25px);
        pointer-events: none;
    }

    .green-patch {
        position: absolute;
        background: #57ab5a;
        border-radius: 50%;
        opacity: 0.85;
        z-index: 1;
    }

    .patch-a {
        width: 55px;
        height: 40px;
        left: 9%;
        top: 10%;
    }

    .patch-b {
        width: 62px;
        height: 46px;
        right: 9%;
        bottom: 12%;
    }

    .water-tile {
        position: absolute;
        width: 120px;
        height: 38px;
        right: -16px;
        top: 118px;
        background: #74c0fc;
        border-radius: 999px;
        opacity: 0.78;
        transform: rotate(-22deg);
        z-index: 1;
        box-shadow: inset 0 0 0 4px rgba(255,255,255,0.25);
    }

    .district-road {
        position: absolute;
        background: #737b85;
        z-index: 2;
        box-shadow: inset 0 0 0 2px rgba(255,255,255,0.16);
    }

    .road-a {
        width: 160%;
        height: 34px;
        left: -30%;
        top: 58%;
        transform: rotate(-14deg);
    }

    .road-b {
        width: 34px;
        height: 150%;
        left: 46%;
        top: -20%;
        transform: rotate(16deg);
    }

    .road-a::after,
    .road-b::after {
        content: "";
        position: absolute;
        inset: 50% 0 auto 0;
        border-top: 2px dashed rgba(255,255,255,0.75);
        animation: roadDash 2.2s linear infinite;
    }

    @keyframes roadDash {
        from { transform: translateX(0); }
        to { transform: translateX(-30px); }
    }

    .facility-layer {
        position: relative;
        z-index: 4;
        padding: 14px;
        height: 100%;
        display: flex;
        flex-wrap: wrap;
        align-content: flex-start;
        justify-content: center;
        gap: 7px;
    }

    .facility {
        display: inline-flex;
        width: 36px;
        height: 36px;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        filter: drop-shadow(0 5px 4px rgba(27,31,36,0.18));
        transform: scale(0.2) translateY(20px);
        opacity: 0;
        animation: buildingPop 0.55s cubic-bezier(.16,.84,.32,1.32) forwards;
    }

    .base-building {
        width: 42px;
        height: 42px;
        font-size: 32px;
    }

    @keyframes buildingPop {
        0% { opacity: 0; transform: scale(0.2) translateY(20px); }
        75% { opacity: 1; transform: scale(1.14) translateY(-3px); }
        100% { opacity: 1; transform: scale(1) translateY(0); }
    }

    .vehicle-layer {
        position: absolute;
        inset: 0;
        z-index: 5;
        pointer-events: none;
    }

    .vehicle {
        position: absolute;
        left: -15%;
        top: 57%;
        font-size: 24px;
        opacity: 0;
        animation: vehicleMove 4.2s linear infinite;
    }

    .vehicle.police {
        top: 64%;
        animation-duration: 3.8s;
    }

    @keyframes vehicleMove {
        0% { left: -18%; opacity: 0; transform: rotate(-10deg); }
        10% { opacity: 1; }
        85% { opacity: 1; }
        100% { left: 112%; opacity: 0; transform: rotate(-10deg); }
    }

    .citizen-layer {
        position: absolute;
        inset: 0;
        z-index: 6;
        pointer-events: none;
    }

    .citizen {
        position: absolute;
        font-size: 22px;
        opacity: 0;
        animation:
            citizenEnter 0.5s ease forwards,
            citizenWalk 2.6s ease-in-out infinite alternate;
    }

    @keyframes citizenEnter {
        from { opacity: 0; transform: translateY(10px) scale(0.55); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes citizenWalk {
        from { margin-left: -6px; }
        to { margin-left: 8px; }
    }

    .district-status {
        display: grid;
        grid-template-columns: 36px 1fr 50px;
        gap: 10px;
        align-items: center;
        padding: 12px;
        border-radius: 18px;
        border: 1px solid var(--line);
        background: #f6f8fa;
    }

    .mood-face {
        font-size: 27px;
    }

    .mood-label {
        font-size: 11px;
        color: var(--muted);
        font-weight: 900;
        margin-bottom: 6px;
    }

    .mood-bar {
        height: 10px;
        background: #d0d7de;
        border-radius: 999px;
        overflow: hidden;
    }

    .mood-fill {
        width: 0%;
        height: 100%;
        border-radius: 999px;
        background: var(--score-color);
        animation: fillMood 1.2s ease forwards;
        animation-delay: 10.2s;
    }

    @keyframes fillMood {
        to { width: var(--score-width); }
    }

    .mood-score {
        font-size: 16px;
        font-weight: 950;
        text-align: right;
    }

    .energy-board {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 30px;
        padding: 24px;
        box-shadow: 0 12px 30px rgba(27,31,36,0.07);
        margin-bottom: 22px;
    }

    .energy-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
    }

    .energy-card {
        position: relative;
        overflow: hidden;
        min-height: 240px;
        background: #f6f8fa;
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 16px;
        text-align: center;
    }

    .energy-card::before {
        content: "";
        position: absolute;
        inset: auto -20px -40px -20px;
        height: 90px;
        background: #b7e4a8;
        border-radius: 50% 50% 0 0;
        z-index: 0;
    }

    .energy-card-title {
        position: relative;
        z-index: 2;
        font-size: 15px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 5px;
    }

    .energy-card-desc {
        position: relative;
        z-index: 2;
        font-size: 12px;
        color: var(--muted);
        margin-bottom: 12px;
    }

    .energy-icon-field {
        position: relative;
        z-index: 2;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-content: flex-start;
        gap: 8px;
        min-height: 128px;
        padding: 12px;
        background: rgba(255,255,255,0.75);
        border: 1px dashed var(--line);
        border-radius: 18px;
    }

    .energy-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        font-size: 26px;
        opacity: 0;
        transform: scale(0.2) translateY(15px);
        animation: buildingPop 0.55s cubic-bezier(.16,.84,.32,1.32) forwards;
    }

    .analysis-bridge {
        display: grid;
        grid-template-columns: 1fr 64px 1fr;
        gap: 14px;
        align-items: center;
        margin-bottom: 22px;
    }

    .bridge-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 26px;
        padding: 22px 24px;
        min-height: 150px;
        box-shadow: 0 10px 26px rgba(27,31,36,0.07);
    }

    .bridge-title {
        font-size: 21px;
        font-weight: 950;
        margin-bottom: 8px;
    }

    .bridge-desc {
        color: var(--muted);
        line-height: 1.65;
        font-size: 14px;
    }

    .bridge-arrow {
        font-size: 44px;
        text-align: center;
        color: var(--blue);
        font-weight: 950;
        animation: arrowMove 0.85s ease-in-out infinite alternate;
    }

    @keyframes arrowMove {
        from { transform: translateX(0); }
        to { transform: translateX(8px); }
    }

    .final-card {
        background: linear-gradient(135deg, #f0fff4 0%, #ddf4ff 100%);
        border: 1px solid #aceebb;
        border-radius: 30px;
        padding: 28px 30px;
        box-shadow: 0 12px 30px rgba(27,31,36,0.07);
    }

    .final-title {
        font-size: 27px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 10px;
    }

    .final-desc {
        font-size: 15px;
        color: var(--muted);
        line-height: 1.75;
        margin-bottom: 16px;
    }

    .dashboard-button {
        display: inline-block;
        background: var(--blue);
        color: white !important;
        text-decoration: none !important;
        padding: 13px 18px;
        border-radius: 15px;
        font-size: 14px;
        font-weight: 950;
        box-shadow: 0 8px 18px rgba(9,105,218,0.22);
    }

    .dashboard-empty {
        display: inline-block;
        background: rgba(255,255,255,0.78);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 14px 16px;
        font-size: 13px;
        color: var(--muted);
    }

    .speech-bubble {
        position: absolute;
        z-index: 10;
        right: 34px;
        top: 106px;
        max-width: 280px;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 16px 18px;
        box-shadow: 0 12px 26px rgba(27,31,36,0.12);
        animation: bubbleIn 0.7s ease both;
        animation-delay: 8.5s;
        opacity: 0;
    }

    .speech-bubble::after {
        content: "";
        position: absolute;
        left: 28px;
        bottom: -10px;
        width: 20px;
        height: 20px;
        background: #ffffff;
        border-right: 1px solid var(--line);
        border-bottom: 1px solid var(--line);
        transform: rotate(45deg);
    }

    @keyframes bubbleIn {
        from { opacity: 0; transform: translateY(10px) scale(0.96); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    .bubble-title {
        font-size: 15px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 5px;
    }

    .bubble-desc {
        font-size: 13px;
        color: var(--muted);
        line-height: 1.55;
    }

    .source-note {
        margin-top: 12px;
        font-size: 11px;
        color: #8c959f;
        line-height: 1.45;
    }

    @media (max-width: 1150px) {
        .top-content,
        .hud-grid,
        .timeline,
        .city-grid,
        .energy-grid,
        .analysis-bridge {
            grid-template-columns: 1fr;
        }

        .bridge-arrow {
            transform: rotate(90deg);
        }

        .game-title {
            font-size: 32px;
        }

        .speech-bubble {
            position: relative;
            right: auto;
            top: auto;
            margin-top: 16px;
            max-width: none;
        }
    }
    </style>
    """

    top = f"""
    <div class="game-root">
        <section class="game-top">
            <div class="wood-plank"></div>
            <div class="top-content">
                <div>
                    <div class="game-eyebrow">NOVA City Builder Simulation</div>
                    <div class="game-title">내가 설계한 스마트시티를 만들자!</div>
                    <div class="game-desc">
                        예산과 에너지 배분을 선택하면 A~E구역에 건물, 도로, 공원, 경찰, 학교,
                        에너지 설비가 게임처럼 등장합니다. 정량 결과 분석은 뒤의 2차 대시보드에서 확인합니다.
                    </div>
                </div>

                <div class="resource-panel">
                    <div class="resource-row">
                        <div class="resource-icon">💰</div>
                        <div class="resource-name">정책 예산</div>
                        <div class="resource-value">100%</div>
                    </div>
                    <div class="resource-row">
                        <div class="resource-icon">⚡</div>
                        <div class="resource-name">에너지 배분</div>
                        <div class="resource-value">100%</div>
                    </div>
                    <div class="resource-row">
                        <div class="resource-icon">🏙️</div>
                        <div class="resource-name">관리 구역</div>
                        <div class="resource-value">5개</div>
                    </div>
                    <div class="resource-row">
                        <div class="resource-icon">⭐</div>
                        <div class="resource-name">현재 시나리오</div>
                        <div class="resource-value" style="font-size:15px;">{html_lib.escape(preset_choice)}</div>
                    </div>
                </div>
            </div>
        </section>
    """

    hud = f"""
        <section class="hud-grid">
            <div class="hud-card">
                <div class="hud-label">선택된 정책</div>
                <div class="hud-value" style="font-size:24px;">{html_lib.escape(preset_choice)}</div>
                <div class="hud-sub">입력한 비율에 따라 도시 장면이 달라집니다.</div>
            </div>

            <div class="hud-card">
                <div class="hud-label">도시 평균 만족도</div>
                <div class="hud-value">{avg:.1f}점</div>
                <div class="hud-sub">정량 분석은 2차 대시보드에서 자세히 확인합니다.</div>
            </div>

            <div class="hud-card">
                <div class="hud-label">에너지 자립률</div>
                <div class="hud-value">{independence * 100:.1f}%</div>
                <div class="hud-sub">태양광·수소·ESS 설비가 늘수록 높아집니다.</div>
            </div>

            <div class="hud-card">
                <div class="hud-label">도시 상태</div>
                <div class="hud-value" style="color:{warning_color}; font-size:24px;">{warning_text}</div>
                <div class="hud-sub">절감액 환원 {savings * 100:.2f}% · {html_lib.escape(model_source)}</div>
            </div>
        </section>
    """

    quest = """
        <section class="quest-panel">
            <div class="quest-icon">🧭</div>
            <div>
                <div class="quest-title">오늘의 미션: 정책 처치가 도시 구조를 어떻게 바꾸는지 관찰하기</div>
                <div class="quest-desc">
                    복지 예산을 늘리면 병원과 돌봄시설이, 교육 예산을 늘리면 학교와 도서관이,
                    안전 예산을 늘리면 경찰과 CCTV가, 에너지 투자를 늘리면 충전소와 발전 설비가 등장합니다.
                </div>
            </div>
        </section>
    """

    timeline = """
        <section class="timeline">
            <div class="timeline-step">
                <div class="timeline-icon">🎛️</div>
                <div class="timeline-title">1. 정책 투입</div>
                <div class="timeline-desc">예산·에너지 비율 선택</div>
            </div>
            <div class="timeline-step">
                <div class="timeline-icon">🏗️</div>
                <div class="timeline-title">2. 건물 생성</div>
                <div class="timeline-desc">학교·병원·경찰·공원 등장</div>
            </div>
            <div class="timeline-step">
                <div class="timeline-icon">🚌</div>
                <div class="timeline-title">3. 도시 활동</div>
                <div class="timeline-desc">버스·경찰차·시민 이동</div>
            </div>
            <div class="timeline-step">
                <div class="timeline-icon">😊</div>
                <div class="timeline-title">4. 시민 반응</div>
                <div class="timeline-desc">표정과 만족도 게이지 변화</div>
            </div>
            <div class="timeline-step">
                <div class="timeline-icon">📊</div>
                <div class="timeline-title">5. 상세 분석</div>
                <div class="timeline-desc">2차 대시보드에서 결과 확인</div>
            </div>
        </section>
    """

    bridge = f"""
        <section class="analysis-bridge">
            <div class="bridge-card">
                <div class="bridge-title">🎛️ 정책 처치</div>
                <div class="bridge-desc">
                    복지 {welfare}% · 교육 {education}% · 에너지 인프라 {energy_infra}% ·
                    일반 인프라 {general_infra}% · 안전 {safety}%<br>
                    태양광 {solar}% · 수소 {hydrogen}% · ESS {ess}% · 외부전력망 {external}%
                </div>
            </div>

            <div class="bridge-arrow">→</div>

            <div class="bridge-card">
                <div class="bridge-title">🏙️ 도시 구조 변화</div>
                <div class="bridge-desc">
                    배분값이 높을수록 관련 시설이 더 많이 등장합니다.
                    구역마다 시민 구성이 다르기 때문에 같은 정책도 다르게 보입니다.
                </div>
            </div>
        </section>
    """

    city = f"""
        <section class="city-board">
            <div class="cloud one">☁️</div>
            <div class="cloud two">☁️</div>

            <div class="map-container">
                <div class="section-heading">
                    <div>
                        <div class="section-title">A~E구역 스마트시티 맵</div>
                        <div class="section-subtitle">
                            각 구역은 서로 다른 성격을 가진 도시 공간입니다.
                            예산 처치가 적용되면 시설이 순서대로 생성되고, 시민 표정과 만족도 게이지가 바뀝니다.
                        </div>
                    </div>
                </div>

                <div class="speech-bubble">
                    <div class="bubble-title">시민 반응</div>
                    <div class="bubble-desc">
                        “우리 구역에 필요한 시설이 생겼어요.
                        이제 2차 대시보드에서 실제 만족도 변화를 확인해볼게요!”
                    </div>
                </div>

                <div class="city-grid">
                    {district_html}
                </div>
            </div>
        </section>
    """

    energy = make_energy_zone(solar, hydrogen, ess, external)

    final = f"""
        <section class="final-card">
            <div class="final-title">🎮 1차 게임형 시뮬레이션 완료</div>
            <div class="final-desc">
                이 화면은 정책 처치가 도시 공간에 어떻게 구현되는지 보여주는 장면형 시뮬레이션입니다.
                다음 단계에서는 같은 입력값을 바탕으로 2차 대시보드에서 시민 만족도,
                에너지 자립률, 구역별 격차, 시나리오 비교를 분석합니다.
            </div>
            {dashboard_button}
            <div class="source-note">
                이 게임형 화면은 기존 classes.py OOP 모델의 결과값을 보조적으로 사용하되,
                핵심 목적은 정량 분석이 아니라 “정책 처치가 도시 장면으로 바뀌는 과정”을 보여주는 것입니다.
            </div>
        </section>
    """

    return css + top + hud + quest + timeline + bridge + city + energy + final + "</div>"


# ==================================================
# Streamlit 전체 CSS
# ==================================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #ffffff;
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

    .main-title {
        font-size: 34px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 6px;
    }

    .main-subtitle {
        font-size: 15px;
        color: #57606a;
        line-height: 1.65;
        margin-bottom: 16px;
    }

    .guide-box {
        background: #fff8c5;
        border: 1px solid #f0d66b;
        border-radius: 16px;
        padding: 16px 18px;
        color: #1f2328;
        line-height: 1.65;
        margin-bottom: 18px;
    }

    .alert-danger-custom {
        background: rgba(207, 34, 46, 0.08);
        border: 1px solid rgba(207, 34, 46, 0.3);
        border-left: 4px solid #cf222e;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #82071e;
        font-size: 14px;
    }

    .alert-success-custom {
        background: rgba(26, 127, 55, 0.08);
        border: 1px solid rgba(26, 127, 55, 0.3);
        border-left: 4px solid #1a7f37;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #0f5323;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# Streamlit 사이드바
# ==================================================
with st.sidebar:
    st.markdown("## 🎮 도시 건설 시뮬레이터")
    st.caption("정책 처치가 A~E구역의 도시 장면을 어떻게 바꾸는지 게임처럼 보여줍니다.")

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
        st.markdown(
            f'<div class="alert-success-custom">예산 합계: {budget_total}% ✓</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="alert-danger-custom">예산 합계: {budget_total}% · 정확히 100% 필요</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### ⚡ 에너지 배분")

    solar = st.slider("태양광", 0, 100, pv("solar", 40), 1, key=f"sol_{preset_key}")
    hydrogen = st.slider("수소연료전지", 0, 100, pv("hydrogen", 35), 1, key=f"hyd_{preset_key}")
    ess = st.slider("ESS", 0, 100, pv("ess", 20), 1, key=f"ess_{preset_key}")
    external = st.slider("외부전력망", 0, 100, pv("external", 5), 1, key=f"ext_{preset_key}")

    energy_total = solar + hydrogen + ess + external
    energy_ok = energy_total == 100

    if energy_ok:
        st.markdown(
            f'<div class="alert-success-custom">에너지 합계: {energy_total}% ✓</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="alert-danger-custom">에너지 합계: {energy_total}% · 정확히 100% 필요</div>',
            unsafe_allow_html=True
        )

    predicted_rate = expected_energy_self_rate(solar, hydrogen, ess, external)

    st.info(
        f"예상 에너지 자립률: {predicted_rate * 100:.1f}%\n\n"
        "태양광×0.7 + 수소연료전지×0.9 + ESS×0.6 + 외부전력망×0.0"
    )

    st.markdown("---")

    default_dashboard_url = get_dashboard_url_from_secrets()
    dashboard_url = st.text_input(
        "2차 대시보드 URL",
        value=default_dashboard_url,
        placeholder="예: https://your-dashboard.streamlit.app",
    )
    st.caption("기존 dashboard.py를 별도 앱으로 배포했다면 그 URL을 입력하세요.")

    st.markdown("---")
    st.info("비율을 바꾸면 도시 맵이 다시 생성됩니다. 건물은 배분값에 따라 많아지거나 줄어듭니다.")


# ==================================================
# 메인 Streamlit 화면
# ==================================================
st.markdown(
    """
    <div class="main-title">🎮 NOVA시 게임형 스마트시티 시뮬레이션</div>
    <div class="main-subtitle">
        이 화면은 최종 분석 대시보드가 아니라, 정책 처치가 도시 구조를 바꾸는 과정을
        마을 만들기 게임처럼 보여주는 1차 시뮬레이션입니다.
    </div>
    """,
    unsafe_allow_html=True,
)

if not HAS_CLASSES:
    st.warning(
        "classes.py를 불러오지 못했습니다. 그래도 화면용 보조 계산으로 게임형 시뮬레이션은 표시됩니다. "
        f"오류 내용: {IMPORT_ERROR_MESSAGE}"
    )

if not budget_ok or not energy_ok:
    st.markdown(
        """
        <div class="guide-box">
            <b>시뮬레이션 실행 조건</b><br>
            예산 배분 합계와 에너지 배분 합계가 각각 정확히 100%가 되어야 합니다.
            왼쪽 사이드바에서 비율을 조정하면 도시 건설 화면이 나타납니다.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

model_result = run_model_or_fallback(
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external,
)

game_html = make_game_html(
    preset_choice,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external,
    model_result,
    dashboard_url,
)

components.html(
    game_html,
    height=1950,
    scrolling=True,
)

st.markdown("### 발표 연결 문장 예시")
st.markdown(
    """
    이 1차 시뮬레이션은 예산과 에너지 배분이 도시 안에서 어떤 시설로 구현되는지를 게임처럼 보여줍니다.  
    이제 같은 입력값을 2차 대시보드에서 확인하면서, 실제 시민 만족도와 에너지 자립률이 어떻게 달라졌는지 분석하겠습니다.
    """
)
