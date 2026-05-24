"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOVA시 고도화 게임형 스마트시티 시뮬레이션
simulation_story.py

역할:
- 기존 dashboard.py는 2차 정량 분석 대시보드로 유지
- 이 파일은 1차 게임형 시각화 앱
- 예산·에너지 배분을 바꾸면 하나의 거대한 마을 맵에서
  건물, 시민, 도로, 에너지 설비, 만족도 반응이 함께 변화함

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
import math
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
    IMPORT_ERROR_MESSAGE = ""
except Exception as import_error:
    HAS_CLASSES = False
    IMPORT_ERROR_MESSAGE = str(import_error)


# ==================================================
# 페이지 설정
# ==================================================
st.set_page_config(
    page_title="NOVA시 게임형 스마트시티 시뮬레이션",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# dashboard.py와 같은 프리셋
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


# 하나의 큰 지도 안에서 각 구역이 차지하는 위치
# x, y, w, h는 CSS absolute position 기준
DISTRICT_INFO = {
    "A구역(산업단지)": {
        "short": "A",
        "label": "A구역 산업단지",
        "main_icon": "🏭",
        "desc": "근로자 중심 · 이동성·일자리 민감",
        "x": 68,
        "y": 405,
        "w": 255,
        "h": 220,
        "theme": "industry",
        "base_icons": ["🏭", "🏢", "🏗️"],
        "people": ["👷", "👩‍🏭", "🧑‍💼", "👨‍🔧"],
        "weights": {
            "welfare": 0.45,
            "education": 0.35,
            "energy_infra": 1.25,
            "general_infra": 1.35,
            "safety": 0.85,
        },
    },

    "B구역(대학가)": {
        "short": "B",
        "label": "B구역 대학가",
        "main_icon": "🎓",
        "desc": "학생 중심 · 교육·문화 민감",
        "x": 328,
        "y": 135,
        "w": 275,
        "h": 220,
        "theme": "campus",
        "base_icons": ["🏫", "🏛️", "🏠"],
        "people": ["🧑‍🎓", "👩‍🎓", "🧑‍💻", "📚"],
        "weights": {
            "welfare": 0.35,
            "education": 1.60,
            "energy_infra": 0.55,
            "general_infra": 0.90,
            "safety": 0.65,
        },
    },

    "C구역(복지타운)": {
        "short": "C",
        "label": "C구역 복지타운",
        "main_icon": "🏥",
        "desc": "노인·취약계층 중심 · 복지·안전 민감",
        "x": 860,
        "y": 130,
        "w": 285,
        "h": 235,
        "theme": "welfare",
        "base_icons": ["🏥", "🏘️", "🏠"],
        "people": ["👵", "👴", "👩‍⚕️", "🧓"],
        "weights": {
            "welfare": 1.65,
            "education": 0.35,
            "energy_infra": 0.55,
            "general_infra": 0.70,
            "safety": 1.10,
        },
    },

    "D구역(신도시)": {
        "short": "D",
        "label": "D구역 신도시",
        "main_icon": "🏙️",
        "desc": "혼합형 시민 구성 · 균형 정책 반응",
        "x": 555,
        "y": 395,
        "w": 300,
        "h": 240,
        "theme": "newtown",
        "base_icons": ["🏙️", "🏢", "🏬"],
        "people": ["👨‍👩‍👧", "🧑‍💼", "👩‍💻", "🧑"],
        "weights": {
            "welfare": 0.90,
            "education": 0.90,
            "energy_infra": 1.05,
            "general_infra": 1.05,
            "safety": 0.90,
        },
    },

    "E구역(구도심)": {
        "short": "E",
        "label": "E구역 구도심",
        "main_icon": "🏚️",
        "desc": "노후 인프라 · 복지·안전·생활SOC 민감",
        "x": 930,
        "y": 430,
        "w": 270,
        "h": 225,
        "theme": "oldtown",
        "base_icons": ["🏚️", "🏠", "🏘️"],
        "people": ["🧑", "👵", "👴", "👨‍👩‍👧"],
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
# 기존 dashboard.py와 동일한 도시 생성
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

    # 보조 계산: 실제 모델이 실패해도 발표 화면은 유지되도록 함
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
# 시각화 유틸
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


def icon_count(value, weight=1.0, max_icons=9, divisor=10):
    count = round((value * weight) / divisor)
    return clamp(count, 0, max_icons)


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


def local_positions(count, width, height, start_x=18, start_y=36):
    positions = []
    if count <= 0:
        return positions

    cols = 4
    gap_x = max(34, (width - 45) / cols)
    gap_y = 39

    for i in range(count):
        col = i % cols
        row = i // cols
        x = start_x + col * gap_x + (row % 2) * 9
        y = start_y + row * gap_y
        x = min(width - 42, x)
        y = min(height - 78, y)
        positions.append((x, y))

    return positions


def make_building(
    icon,
    label,
    x,
    y,
    delay,
    category,
    size="normal",
):
    return f"""
    <div class="building building-{category} building-{size}"
         style="left:{x:.1f}px; top:{y:.1f}px; animation-delay:{delay:.2f}s;"
         title="{html_lib.escape(label)}">
        <div class="building-shadow"></div>
        <div class="building-icon">{icon}</div>
    </div>
    """


def make_district_buildings(
    district_key,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    idx,
):
    info = DISTRICT_INFO[district_key]
    weights = info["weights"]
    w = info["w"]
    h = info["h"]

    buildings = []

    base_positions = local_positions(3, w, h, start_x=18, start_y=34)
    for i, (x, y) in enumerate(base_positions):
        icon = info["base_icons"][i % len(info["base_icons"])]
        buildings.append(
            make_building(
                icon=icon,
                label=f"{info['label']} 기본 건물",
                x=x,
                y=y,
                delay=0.4 + idx * 0.08 + i * 0.12,
                category="base",
                size="large",
            )
        )

    categories = [
        {
            "name": "welfare",
            "value": welfare,
            "weight": weights["welfare"],
            "icons": ["🏥", "👩‍⚕️", "🏘️", "🤝"],
            "label": "복지 시설",
            "delay": 1.4,
            "start_x": 20,
            "start_y": 102,
        },
        {
            "name": "education",
            "value": education,
            "weight": weights["education"],
            "icons": ["🏫", "📚", "🎓", "🏛️"],
            "label": "교육 시설",
            "delay": 2.2,
            "start_x": 70,
            "start_y": 100,
        },
        {
            "name": "energy",
            "value": energy_infra,
            "weight": weights["energy_infra"],
            "icons": ["🔌", "📡", "🚗", "💡"],
            "label": "에너지 인프라",
            "delay": 3.0,
            "start_x": 122,
            "start_y": 98,
        },
        {
            "name": "infra",
            "value": general_infra,
            "weight": weights["general_infra"],
            "icons": ["🌳", "🚏", "🏞️", "🚌", "🛣️"],
            "label": "생활 인프라",
            "delay": 3.8,
            "start_x": 40,
            "start_y": 154,
        },
        {
            "name": "safety",
            "value": safety,
            "weight": weights["safety"],
            "icons": ["👮", "📹", "🚒", "🚓", "🛡️"],
            "label": "안전 시설",
            "delay": 4.6,
            "start_x": 104,
            "start_y": 154,
        },
    ]

    for cat in categories:
        count = icon_count(cat["value"], cat["weight"], max_icons=7, divisor=10)
        positions = local_positions(
            count,
            w,
            h,
            start_x=cat["start_x"],
            start_y=cat["start_y"],
        )
        icon_cycle = cycle(cat["icons"])

        for j, (x, y) in enumerate(positions):
            buildings.append(
                make_building(
                    icon=next(icon_cycle),
                    label=cat["label"],
                    x=x,
                    y=y,
                    delay=cat["delay"] + idx * 0.10 + j * 0.09,
                    category=cat["name"],
                )
            )

    return "".join(buildings)


def make_citizens_for_district(district_key, score, idx):
    info = DISTRICT_INFO[district_key]
    people_cycle = cycle(info["people"])
    face = score_face(score)
    color = score_color(score)

    citizens = []

    for i in range(9):
        person = next(people_cycle)
        delay = 6.8 + idx * 0.18 + i * 0.14
        x = 18 + (i * 23) % max(120, info["w"] - 40)
        y = info["h"] - 54 - (i % 3) * 10
        walk = 14 + (i % 4) * 8

        citizens.append(
            f"""
            <div class="villager"
                 style="
                    left:{x:.1f}px;
                    top:{y:.1f}px;
                    --walk:{walk}px;
                    --mood-color:{color};
                    animation-delay:{delay:.2f}s;
                 ">
                <div class="villager-face">{person}</div>
                <div class="villager-mood">{face}</div>
            </div>
            """
        )

    return "".join(citizens)


def make_district_zone(
    district_key,
    score,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    idx,
):
    info = DISTRICT_INFO[district_key]
    color = score_color(score)
    face = score_face(score)
    mood = score_mood(score)

    buildings = make_district_buildings(
        district_key,
        welfare,
        education,
        energy_infra,
        general_infra,
        safety,
        idx,
    )

    citizens = make_citizens_for_district(district_key, score, idx)

    return f"""
    <div class="district-zone zone-{idx + 1}"
         style="
            left:{info['x']}px;
            top:{info['y']}px;
            width:{info['w']}px;
            height:{info['h']}px;
         ">
        <div class="zone-label">
            <div class="zone-main-icon">{info['main_icon']}</div>
            <div>
                <div class="zone-title">{info['label']}</div>
                <div class="zone-desc">{info['desc']}</div>
            </div>
        </div>

        <div class="zone-ground">
            <div class="mini-road road-horizontal"></div>
            <div class="mini-road road-vertical"></div>
            {buildings}
            {citizens}
        </div>

        <div class="zone-score">
            <div class="score-face">{face}</div>
            <div class="score-mid">
                <div class="score-label">시민 만족도 · {mood}</div>
                <div class="score-bar">
                    <div class="score-fill"
                         style="--score-width:{score:.1f}%; --score-color:{color};">
                    </div>
                </div>
            </div>
            <div class="score-num" style="color:{color};">{score:.1f}</div>
        </div>
    </div>
    """


def make_vehicle_stream(general_infra, safety):
    bus_count = icon_count(general_infra, 1.0, max_icons=5, divisor=16)
    police_count = icon_count(safety, 1.0, max_icons=4, divisor=18)

    html = ""

    for i in range(bus_count):
        delay = i * 1.25
        html += f"""
        <div class="world-vehicle bus"
             style="top:{392 + (i % 2) * 26}px; animation-delay:{delay:.2f}s;">
            🚌
        </div>
        """

    for i in range(police_count):
        delay = 0.7 + i * 1.35
        html += f"""
        <div class="world-vehicle police"
             style="top:{642 + (i % 2) * 22}px; animation-delay:{delay:.2f}s;">
            🚓
        </div>
        """

    return html


def make_energy_facility_icon(icon, label, x, y, delay):
    return f"""
    <div class="energy-building"
         style="left:{x}px; top:{y}px; animation-delay:{delay:.2f}s;"
         title="{html_lib.escape(label)}">
        <div class="energy-building-icon">{icon}</div>
    </div>
    """


def make_energy_world(solar, hydrogen, ess, external):
    html = ""

    solar_count = icon_count(solar, 1.15, max_icons=9, divisor=9)
    hydrogen_count = icon_count(hydrogen, 1.15, max_icons=8, divisor=9)
    ess_count = icon_count(ess, 1.20, max_icons=8, divisor=9)
    external_count = icon_count(external, 1.0, max_icons=7, divisor=10)

    for i in range(solar_count):
        x = 55 + (i % 5) * 44
        y = 72 + (i // 5) * 42
        html += make_energy_facility_icon("☀️", "태양광 설비", x, y, 5.3 + i * 0.08)

    for i in range(hydrogen_count):
        x = 965 + (i % 4) * 48
        y = 58 + (i // 4) * 44
        html += make_energy_facility_icon("💧", "수소연료전지", x, y, 5.7 + i * 0.08)

    for i in range(ess_count):
        x = 1040 + (i % 4) * 42
        y = 715 + (i // 4) * 38
        html += make_energy_facility_icon("🔋", "ESS 저장소", x, y, 6.1 + i * 0.08)

    for i in range(external_count):
        x = 55 + (i % 4) * 46
        y = 712 + (i // 4) * 40
        html += make_energy_facility_icon("🗼", "외부전력망", x, y, 6.5 + i * 0.08)

    return html


def make_need_summary_cards(welfare, education, energy_infra, general_infra, safety):
    items = [
        ("복지", welfare, "🏥", "병원·돌봄센터·복지관"),
        ("교육", education, "🏫", "학교·도서관·평생학습"),
        ("에너지 인프라", energy_infra, "🔌", "충전소·스마트그리드"),
        ("일반 인프라", general_infra, "🚌", "도로·버스·공원"),
        ("안전", safety, "👮", "경찰·CCTV·소방"),
    ]

    html = ""

    for label, value, icon, desc in items:
        html += f"""
        <div class="policy-card">
            <div class="policy-icon">{icon}</div>
            <div class="policy-name">{label}</div>
            <div class="policy-value">{value}%</div>
            <div class="policy-bar">
                <div class="policy-fill" style="width:{value}%;"></div>
            </div>
            <div class="policy-desc">{desc}</div>
        </div>
        """

    return html


def make_energy_summary_cards(solar, hydrogen, ess, external):
    items = [
        ("태양광", solar, "☀️", "지붕형 패널·분산 발전"),
        ("수소연료전지", hydrogen, "💧", "안정형 발전 설비"),
        ("ESS", ess, "🔋", "에너지 저장 시설"),
        ("외부전력망", external, "🗼", "도시 외부 의존"),
    ]

    html = ""

    for label, value, icon, desc in items:
        html += f"""
        <div class="energy-policy-card">
            <div class="policy-icon">{icon}</div>
            <div class="policy-name">{label}</div>
            <div class="policy-value">{value}%</div>
            <div class="policy-bar">
                <div class="policy-fill energy-fill" style="width:{value}%;"></div>
            </div>
            <div class="policy-desc">{desc}</div>
        </div>
        """

    return html


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
        district_html += make_district_zone(
            key,
            scores[key],
            welfare,
            education,
            energy_infra,
            general_infra,
            safety,
            idx,
        )

    vehicles = make_vehicle_stream(general_infra, safety)
    energy_world = make_energy_world(solar, hydrogen, ess, external)

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

    policy_cards = make_need_summary_cards(
        welfare,
        education,
        energy_infra,
        general_infra,
        safety,
    )

    energy_cards = make_energy_summary_cards(
        solar,
        hydrogen,
        ess,
        external,
    )

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
        --grass: #a8db98;
        --grass2: #b7e4a8;
        --road: #6e7781;
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
        min-height: 250px;
        padding: 32px 36px;
        color: white;
        background:
            radial-gradient(circle at 12% 25%, rgba(255,255,255,0.20), transparent 18%),
            radial-gradient(circle at 88% 20%, rgba(255,255,255,0.16), transparent 20%),
            linear-gradient(135deg, #9a5a2f 0%, #c77936 42%, #e2a24d 100%);
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
        grid-template-columns: 42px 1fr 88px;
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

    .policy-summary-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 18px;
    }

    .policy-card,
    .energy-policy-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 14px 14px;
        min-height: 142px;
        box-shadow: 0 8px 20px rgba(27,31,36,0.05);
    }

    .policy-icon {
        font-size: 26px;
        margin-bottom: 6px;
    }

    .policy-name {
        font-size: 13px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 4px;
    }

    .policy-value {
        font-size: 22px;
        font-weight: 950;
        color: var(--blue);
        margin-bottom: 8px;
    }

    .policy-bar {
        height: 8px;
        background: #d0d7de;
        border-radius: 999px;
        overflow: hidden;
        margin-bottom: 7px;
    }

    .policy-fill {
        height: 100%;
        background: linear-gradient(90deg, #0969da, #8250df);
        border-radius: 999px;
    }

    .energy-fill {
        background: linear-gradient(90deg, #1a7f37, #d29922);
    }

    .policy-desc {
        font-size: 11px;
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

    .world-board {
        position: relative;
        width: 1280px;
        height: 860px;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 34px;
        margin-bottom: 24px;
        background:
            linear-gradient(180deg, #ddf4ff 0%, #ecf8ff 22%, #eaf8e1 55%, #cce6b6 100%);
        box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.8),
            0 18px 42px rgba(27,31,36,0.10);
    }

    .world-board::before {
        content: "☀️";
        position: absolute;
        top: 22px;
        right: 34px;
        font-size: 62px;
        animation: sunSpin 14s linear infinite;
        z-index: 4;
    }

    @keyframes sunSpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .mountain {
        position: absolute;
        font-size: 82px;
        opacity: 0.88;
        z-index: 1;
        filter: drop-shadow(0 8px 8px rgba(27,31,36,0.12));
    }

    .mountain.m1 { left: 1010px; top: 12px; }
    .mountain.m2 { left: 1070px; top: 6px; }
    .mountain.m3 { left: 1140px; top: 20px; }

    .cloud {
        position: absolute;
        font-size: 42px;
        opacity: 0.72;
        z-index: 3;
        animation: cloudMove 12s ease-in-out infinite alternate;
    }

    .cloud.c1 { left: 110px; top: 48px; }
    .cloud.c2 { left: 520px; top: 70px; animation-delay: 1.5s; }
    .cloud.c3 { left: 795px; top: 35px; animation-delay: 2.3s; }

    @keyframes cloudMove {
        from { transform: translateX(0); }
        to { transform: translateX(48px); }
    }

    .river {
        position: absolute;
        left: -80px;
        top: 610px;
        width: 1500px;
        height: 88px;
        background:
            repeating-linear-gradient(
                115deg,
                rgba(255,255,255,0.35) 0 10px,
                rgba(255,255,255,0.05) 10px 22px
            ),
            #74c0fc;
        transform: rotate(-7deg);
        border-radius: 999px;
        opacity: 0.88;
        z-index: 1;
        box-shadow: inset 0 0 0 6px rgba(255,255,255,0.18);
    }

    .world-road {
        position: absolute;
        background: #737b85;
        z-index: 2;
        box-shadow: inset 0 0 0 2px rgba(255,255,255,0.18);
    }

    .world-road.r1 {
        left: -80px;
        top: 382px;
        width: 1470px;
        height: 46px;
        transform: rotate(-7deg);
    }

    .world-road.r2 {
        left: 420px;
        top: -40px;
        width: 50px;
        height: 1000px;
        transform: rotate(12deg);
    }

    .world-road.r3 {
        left: 800px;
        top: 0;
        width: 48px;
        height: 980px;
        transform: rotate(-14deg);
    }

    .world-road.r4 {
        left: -100px;
        top: 660px;
        width: 1500px;
        height: 42px;
        transform: rotate(4deg);
    }

    .world-road::after {
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        width: 2200px;
        border-top: 3px dashed rgba(255,255,255,0.75);
        animation: roadDash 2.2s linear infinite;
    }

    @keyframes roadDash {
        from { transform: translateX(0); }
        to { transform: translateX(-60px); }
    }

    .tree {
        position: absolute;
        font-size: 34px;
        z-index: 3;
        filter: drop-shadow(0 5px 4px rgba(27,31,36,0.12));
    }

    .tree.t1 { left: 35px; top: 185px; }
    .tree.t2 { left: 90px; top: 245px; }
    .tree.t3 { left: 150px; top: 178px; }
    .tree.t4 { left: 670px; top: 105px; }
    .tree.t5 { left: 725px; top: 165px; }
    .tree.t6 { left: 1200px; top: 350px; }
    .tree.t7 { left: 1110px; top: 365px; }
    .tree.t8 { left: 420px; top: 690px; }
    .tree.t9 { left: 500px; top: 730px; }
    .tree.t10 { left: 1180px; top: 730px; }

    .world-label {
        position: absolute;
        left: 34px;
        top: 28px;
        z-index: 5;
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(208,215,222,0.9);
        border-radius: 22px;
        padding: 16px 18px;
        box-shadow: 0 10px 24px rgba(27,31,36,0.10);
    }

    .world-label-title {
        font-size: 23px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 4px;
    }

    .world-label-desc {
        font-size: 13px;
        color: var(--muted);
        line-height: 1.55;
    }

    .district-zone {
        position: absolute;
        z-index: 10;
        border-radius: 24px;
        border: 2px solid rgba(255,255,255,0.85);
        background:
            linear-gradient(135deg, rgba(255,255,255,0.52), rgba(255,255,255,0.22)),
            repeating-linear-gradient(45deg, #b7e4a8 0 18px, #a8db98 18px 36px);
        box-shadow:
            0 14px 28px rgba(27,31,36,0.15),
            inset 0 0 0 1px rgba(0,0,0,0.05);
        overflow: hidden;
        animation: zoneAppear 0.85s ease both;
    }

    .zone-1 { animation-delay: 0.2s; }
    .zone-2 { animation-delay: 0.35s; }
    .zone-3 { animation-delay: 0.50s; }
    .zone-4 { animation-delay: 0.65s; }
    .zone-5 { animation-delay: 0.80s; }

    @keyframes zoneAppear {
        from {
            opacity: 0;
            transform: translateY(18px) scale(0.97);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    .zone-label {
        position: absolute;
        left: 10px;
        top: 10px;
        right: 10px;
        z-index: 20;
        display: grid;
        grid-template-columns: 38px 1fr;
        gap: 8px;
        align-items: center;
        padding: 8px 10px;
        background: rgba(255,255,255,0.90);
        border: 1px solid rgba(208,215,222,0.9);
        border-radius: 16px;
        box-shadow: 0 6px 14px rgba(27,31,36,0.08);
    }

    .zone-main-icon {
        width: 34px;
        height: 34px;
        border-radius: 13px;
        background: #f6f8fa;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 21px;
    }

    .zone-title {
        font-size: 13px;
        font-weight: 950;
        color: var(--ink);
        margin-bottom: 2px;
    }

    .zone-desc {
        font-size: 10px;
        color: var(--muted);
        line-height: 1.25;
    }

    .zone-ground {
        position: absolute;
        inset: 0;
        z-index: 12;
    }

    .mini-road {
        position: absolute;
        background: rgba(115,123,133,0.75);
        z-index: 13;
        box-shadow: inset 0 0 0 2px rgba(255,255,255,0.16);
    }

    .road-horizontal {
        left: -30px;
        top: 60%;
        width: 140%;
        height: 28px;
        transform: rotate(-9deg);
    }

    .road-vertical {
        left: 47%;
        top: 0;
        width: 26px;
        height: 120%;
        transform: rotate(13deg);
    }

    .building {
        position: absolute;
        z-index: 18;
        width: 36px;
        height: 36px;
        opacity: 0;
        transform: translateY(22px) scale(0.2);
        animation: buildingPop 0.56s cubic-bezier(.16,.84,.32,1.32) forwards;
    }

    .building-large {
        width: 44px;
        height: 44px;
    }

    .building-shadow {
        position: absolute;
        left: 5px;
        bottom: -3px;
        width: 28px;
        height: 9px;
        background: rgba(27,31,36,0.20);
        border-radius: 999px;
        filter: blur(1px);
    }

    .building-icon {
        position: relative;
        z-index: 2;
        width: 100%;
        height: 100%;
        font-size: 29px;
        display: flex;
        align-items: center;
        justify-content: center;
        filter: drop-shadow(0 5px 3px rgba(27,31,36,0.20));
    }

    .building-large .building-icon {
        font-size: 35px;
    }

    .building-welfare .building-icon {
        filter: drop-shadow(0 5px 3px rgba(26,127,55,0.22));
    }

    .building-education .building-icon {
        filter: drop-shadow(0 5px 3px rgba(9,105,218,0.22));
    }

    .building-safety .building-icon {
        filter: drop-shadow(0 5px 3px rgba(207,34,46,0.22));
    }

    @keyframes buildingPop {
        0% {
            opacity: 0;
            transform: translateY(22px) scale(0.2);
        }
        72% {
            opacity: 1;
            transform: translateY(-4px) scale(1.16);
        }
        100% {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    .villager {
        position: absolute;
        z-index: 26;
        width: 34px;
        height: 44px;
        opacity: 0;
        animation:
            villagerEnter 0.55s ease forwards,
            villagerWalk 2.8s ease-in-out infinite alternate;
    }

    .villager-face {
        font-size: 24px;
        filter: drop-shadow(0 4px 3px rgba(27,31,36,0.22));
    }

    .villager-mood {
        position: absolute;
        right: -8px;
        top: -10px;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: #ffffff;
        border: 2px solid var(--mood-color);
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 8px rgba(27,31,36,0.18);
    }

    @keyframes villagerEnter {
        from {
            opacity: 0;
            transform: translateY(10px) scale(0.5);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @keyframes villagerWalk {
        from {
            margin-left: calc(var(--walk) * -0.4);
            margin-top: 0;
        }
        to {
            margin-left: var(--walk);
            margin-top: -4px;
        }
    }

    .zone-score {
        position: absolute;
        left: 10px;
        right: 10px;
        bottom: 9px;
        z-index: 30;
        display: grid;
        grid-template-columns: 32px 1fr 48px;
        gap: 8px;
        align-items: center;
        padding: 8px 9px;
        border-radius: 15px;
        border: 1px solid rgba(208,215,222,0.95);
        background: rgba(255,255,255,0.92);
        box-shadow: 0 6px 14px rgba(27,31,36,0.10);
    }

    .score-face {
        font-size: 23px;
    }

    .score-label {
        font-size: 10px;
        color: var(--muted);
        font-weight: 900;
        margin-bottom: 5px;
    }

    .score-bar {
        height: 8px;
        background: #d0d7de;
        border-radius: 999px;
        overflow: hidden;
    }

    .score-fill {
        width: 0%;
        height: 100%;
        background: var(--score-color);
        border-radius: 999px;
        animation: fillScore 1.2s ease forwards;
        animation-delay: 9.3s;
    }

    @keyframes fillScore {
        to {
            width: var(--score-width);
        }
    }

    .score-num {
        font-size: 15px;
        font-weight: 950;
        text-align: right;
    }

    .energy-building {
        position: absolute;
        z-index: 11;
        width: 42px;
        height: 42px;
        opacity: 0;
        transform: translateY(20px) scale(0.2);
        animation: energyPop 0.56s cubic-bezier(.16,.84,.32,1.32) forwards;
    }

    .energy-building-icon {
        font-size: 33px;
        filter: drop-shadow(0 5px 3px rgba(27,31,36,0.20));
    }

    @keyframes energyPop {
        0% {
            opacity: 0;
            transform: translateY(20px) scale(0.2);
        }
        72% {
            opacity: 1;
            transform: translateY(-4px) scale(1.12);
        }
        100% {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    .world-vehicle {
        position: absolute;
        left: -80px;
        z-index: 40;
        font-size: 28px;
        animation: worldVehicleMove 7s linear infinite;
        opacity: 0;
    }

    .world-vehicle.police {
        animation-duration: 6.2s;
    }

    @keyframes worldVehicleMove {
        0% {
            left: -80px;
            opacity: 0;
            transform: rotate(-7deg);
        }
        8% {
            opacity: 1;
        }
        88% {
            opacity: 1;
        }
        100% {
            left: 1360px;
            opacity: 0;
            transform: rotate(-7deg);
        }
    }

    .speech-bubble {
        position: absolute;
        z-index: 60;
        right: 42px;
        top: 220px;
        max-width: 290px;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 16px 18px;
        box-shadow: 0 12px 26px rgba(27,31,36,0.14);
        opacity: 0;
        animation: bubbleIn 0.7s ease forwards;
        animation-delay: 8.5s;
    }

    .speech-bubble::after {
        content: "";
        position: absolute;
        left: 30px;
        bottom: -10px;
        width: 20px;
        height: 20px;
        background: #ffffff;
        border-right: 1px solid var(--line);
        border-bottom: 1px solid var(--line);
        transform: rotate(45deg);
    }

    @keyframes bubbleIn {
        from {
            opacity: 0;
            transform: translateY(10px) scale(0.96);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
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

    .energy-summary-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 18px;
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

    .source-note {
        margin-top: 12px;
        font-size: 11px;
        color: #8c959f;
        line-height: 1.45;
    }

    .map-scroll-hint {
        margin-bottom: 10px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.5;
    }

    .world-scroll {
        width: 100%;
        overflow-x: auto;
        padding-bottom: 12px;
    }

    @media (max-width: 1150px) {
        .top-content,
        .hud-grid,
        .policy-summary-grid,
        .energy-summary-grid,
        .analysis-bridge {
            grid-template-columns: 1fr;
        }

        .game-title {
            font-size: 32px;
        }

        .bridge-arrow {
            transform: rotate(90deg);
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
                        예산과 에너지 배분을 조정하면 하나의 거대한 NOVA시 지도에서
                        A~E구역의 건물, 시민, 교통, 에너지 설비, 만족도 반응이 함께 바뀝니다.
                        정량 분석은 2차 대시보드에서 이어서 확인합니다.
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
                <div class="hud-sub">입력한 비율에 따라 마을 장면이 다시 생성됩니다.</div>
            </div>

            <div class="hud-card">
                <div class="hud-label">도시 평균 만족도</div>
                <div class="hud-value">{avg:.1f}점</div>
                <div class="hud-sub">지도에서는 시민 표정과 구역 게이지로 표현됩니다.</div>
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
                <div class="quest-title">오늘의 미션: 정책 처치가 마을 사람들의 삶을 어떻게 바꾸는지 관찰하기</div>
                <div class="quest-desc">
                    복지 예산을 늘리면 병원과 돌봄시설이, 교육 예산을 늘리면 학교와 도서관이,
                    안전 예산을 늘리면 경찰과 CCTV가, 인프라 예산을 늘리면 버스와 공원이,
                    에너지 투자를 늘리면 충전소와 발전 설비가 생깁니다.
                </div>
            </div>
        </section>
    """

    policy = f"""
        <section class="policy-summary-grid">
            {policy_cards}
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
                <div class="bridge-title">🏙️ 거대한 마을 환경 변화</div>
                <div class="bridge-desc">
                    같은 예산이라도 구역의 성격에 따라 다르게 표현됩니다.
                    대학가는 교육 예산에, 복지타운은 복지와 안전 예산에,
                    산업단지는 인프라와 에너지 예산에 더 민감하게 반응합니다.
                </div>
            </div>
        </section>
    """

    world = f"""
        <div class="map-scroll-hint">
            지도가 넓게 구성되어 있습니다. 화면이 좁으면 가로로 스크롤해서 전체 NOVA시를 확인할 수 있습니다.
        </div>

        <div class="world-scroll">
            <section class="world-board">
                <div class="world-label">
                    <div class="world-label-title">NOVA시 통합 마을 맵</div>
                    <div class="world-label-desc">
                        A~E구역이 하나의 도시 안에서 연결되어 있고,
                        정책 비율에 따라 건물·시민·차량·에너지 설비가 변화합니다.
                    </div>
                </div>

                <div class="cloud c1">☁️</div>
                <div class="cloud c2">☁️</div>
                <div class="cloud c3">☁️</div>

                <div class="mountain m1">⛰️</div>
                <div class="mountain m2">⛰️</div>
                <div class="mountain m3">⛰️</div>

                <div class="river"></div>

                <div class="world-road r1"></div>
                <div class="world-road r2"></div>
                <div class="world-road r3"></div>
                <div class="world-road r4"></div>

                <div class="tree t1">🌲</div>
                <div class="tree t2">🌳</div>
                <div class="tree t3">🌲</div>
                <div class="tree t4">🌳</div>
                <div class="tree t5">🌲</div>
                <div class="tree t6">🌳</div>
                <div class="tree t7">🌲</div>
                <div class="tree t8">🌳</div>
                <div class="tree t9">🌲</div>
                <div class="tree t10">🌳</div>

                {energy_world}
                {vehicles}
                {district_html}

                <div class="speech-bubble">
                    <div class="bubble-title">마을 사람들의 반응</div>
                    <div class="bubble-desc">
                        “새로운 시설이 생기고 생활 환경이 달라졌어요.
                        이제 2차 대시보드에서 우리 구역의 실제 만족도 변화를 확인해볼게요!”
                    </div>
                </div>
            </section>
        </div>
    """

    energy_summary = f"""
        <section class="energy-summary-grid">
            {energy_cards}
        </section>
    """

    final = f"""
        <section class="final-card">
            <div class="final-title">🎮 1차 고도화 게임형 시뮬레이션 완료</div>
            <div class="final-desc">
                이 화면은 정책 처치가 하나의 도시 환경 안에서 어떻게 구현되는지 보여주는 장면형 시뮬레이션입니다.
                다음 단계에서는 같은 입력값을 바탕으로 2차 대시보드에서 시민 만족도,
                에너지 자립률, 구역별 격차, 시나리오 비교를 분석합니다.
            </div>
            {dashboard_button}
            <div class="source-note">
                이 게임형 화면은 기존 classes.py OOP 모델의 결과값을 기반으로 시민 표정과 만족도 게이지를 표현합니다.
                완전한 모바일 게임 그래픽 수준으로 만들려면 별도의 건물·도로·캐릭터 이미지 에셋을 추가하면 더 자연스럽게 확장할 수 있습니다.
            </div>
        </section>
    """

    return css + top + hud + quest + policy + bridge + world + energy_summary + final + "</div>"


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
# 사이드바
# ==================================================
with st.sidebar:
    st.markdown("## 🎮 도시 건설 시뮬레이터")
    st.caption("정책 처치가 A~E구역의 거대한 마을 환경을 어떻게 바꾸는지 보여줍니다.")

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
    st.info("슬라이더 값을 바꾸면 마을 전체가 다시 생성됩니다. 건물, 시민 표정, 만족도 게이지가 함께 바뀝니다.")


# ==================================================
# 메인 화면
# ==================================================
st.markdown(
    """
    <div class="main-title">🎮 NOVA시 고도화 게임형 스마트시티 시뮬레이션</div>
    <div class="main-subtitle">
        이 화면은 최종 분석 대시보드가 아니라, 정책 처치가 하나의 거대한 마을 환경을 바꾸는 과정을
        게임처럼 보여주는 1차 시뮬레이션입니다.
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
    height=2050,
    scrolling=True,
)

st.markdown("### 발표 연결 문장 예시")
st.markdown(
    """
    이 1차 시뮬레이션은 예산과 에너지 배분이 도시 안에서 어떤 시설과 생활환경으로 구현되는지를 게임처럼 보여줍니다.  
    이제 같은 입력값을 2차 대시보드에서 확인하면서, 실제 시민 만족도와 에너지 자립률이 어떻게 달라졌는지 분석하겠습니다.
    """
)
