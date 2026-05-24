"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOVA시 아이템형 스마트시티 시뮬레이션
simulation_story.py

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

import streamlit as st
import streamlit.components.v1 as components


# ==================================================
# classes.py import
# ==================================================
sys.path.insert(0, os.path.dirname(__file__))

try:
    from classes import (
        Worker, Student, Caregiver, Unemployed, Elder,
        SolarPanel, HydrogenCell, ESS, ExternalGrid,
        Resource, EnergyGrid, District, City,
        BudgetAllocationError, EnergyAllocationError
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
    page_title="NOVA시 아이템형 스마트시티 시뮬레이션",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# 프리셋
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
        "label": "A구역 산업단지",
        "icon": "🏭",
        "desc": "근로자 중심 · 이동성·에너지·인프라 민감",
        "people": ["👷", "👩‍🏭", "🧑‍💼", "👨‍🔧", "👩‍💼", "👨‍💼"],
        "weights": {
            "welfare": 0.45,
            "education": 0.35,
            "energy_infra": 1.25,
            "general_infra": 1.35,
            "safety": 0.85,
        },
    },
    "B구역(대학가)": {
        "label": "B구역 대학가",
        "icon": "🎓",
        "desc": "학생 중심 · 교육·문화·기회 민감",
        "people": ["🧑‍🎓", "👩‍🎓", "🧑‍💻", "👨‍🎓", "👩‍💻", "📚"],
        "weights": {
            "welfare": 0.35,
            "education": 1.60,
            "energy_infra": 0.55,
            "general_infra": 0.90,
            "safety": 0.65,
        },
    },
    "C구역(복지타운)": {
        "label": "C구역 복지타운",
        "icon": "🏥",
        "desc": "노인·취약계층 중심 · 복지·안전 민감",
        "people": ["👵", "👴", "👩‍⚕️", "🧓", "👨‍⚕️", "🤝"],
        "weights": {
            "welfare": 1.65,
            "education": 0.35,
            "energy_infra": 0.55,
            "general_infra": 0.70,
            "safety": 1.10,
        },
    },
    "D구역(신도시)": {
        "label": "D구역 신도시",
        "icon": "🏙️",
        "desc": "혼합형 시민 구성 · 균형 정책 반응",
        "people": ["👨‍👩‍👧", "🧑‍💼", "👩‍💻", "🧑", "👨‍👩‍👦", "👩"],
        "weights": {
            "welfare": 0.90,
            "education": 0.90,
            "energy_infra": 1.05,
            "general_infra": 1.05,
            "safety": 0.90,
        },
    },
    "E구역(구도심)": {
        "label": "E구역 구도심",
        "icon": "🏘️",
        "desc": "노후 인프라 · 복지·안전·생활SOC 민감",
        "people": ["🧑", "👵", "👴", "👨‍👩‍👧", "👩", "🧓"],
        "weights": {
            "welfare": 1.15,
            "education": 0.55,
            "energy_infra": 0.60,
            "general_infra": 1.10,
            "safety": 1.25,
        },
    },
}


BUDGET_ITEMS = {
    "welfare": {
        "name": "복지",
        "item": "힐링 키트",
        "icon": "💗",
        "object": "🏥",
        "color": "#1a7f37",
        "desc": "의료, 돌봄, 복지관, 취약계층 지원",
    },
    "education": {
        "name": "교육",
        "item": "지식 스크롤",
        "icon": "📘",
        "object": "🏫",
        "color": "#0969da",
        "desc": "학교, 도서관, 직업훈련, 청년 기회",
    },
    "energy_infra": {
        "name": "에너지 인프라",
        "item": "스마트 배터리",
        "icon": "🔋",
        "object": "🔌",
        "color": "#8250df",
        "desc": "스마트그리드, 충전소, 친환경 기반시설",
    },
    "general_infra": {
        "name": "일반 인프라",
        "item": "도시 블록",
        "icon": "🧱",
        "object": "🏞️",
        "color": "#d29922",
        "desc": "도로, 대중교통, 공원, 생활SOC",
    },
    "safety": {
        "name": "안전",
        "item": "보호 방패",
        "icon": "🛡️",
        "object": "👮",
        "color": "#cf222e",
        "desc": "치안, 소방, CCTV, 재난 대응",
    },
}


ENERGY_ITEMS = {
    "solar": {
        "name": "태양광",
        "item": "태양 코어",
        "icon": "☀️",
        "object": "🔆",
        "color": "#f59e0b",
        "desc": "지붕형 패널과 분산 발전",
    },
    "hydrogen": {
        "name": "수소연료전지",
        "item": "수소 셀",
        "icon": "💧",
        "object": "⚗️",
        "color": "#3b82f6",
        "desc": "안정적인 도시 전력 생산",
    },
    "ess": {
        "name": "ESS",
        "item": "저장 배터리",
        "icon": "🔋",
        "object": "⚡",
        "color": "#10b981",
        "desc": "남는 전력을 저장하고 보완",
    },
    "external": {
        "name": "외부전력망",
        "item": "전력 타워",
        "icon": "🗼",
        "object": "🔌",
        "color": "#6b7280",
        "desc": "도시 외부 전력망 의존",
    },
}


# ==================================================
# Streamlit CSS
# ==================================================
st.markdown("""
<style>
.stApp {
    background: #f7f8fb;
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

.app-title {
    font-size: 34px;
    font-weight: 900;
    color: #1f2328;
    margin-bottom: 6px;
}

.app-subtitle {
    font-size: 15px;
    line-height: 1.7;
    color: #57606a;
    margin-bottom: 18px;
}

.box-info {
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 8px 20px rgba(27,31,36,0.05);
    margin-bottom: 14px;
}

.box-warn {
    background: #fff8c5;
    border: 1px solid #f0d66b;
    border-radius: 14px;
    padding: 14px 16px;
    color: #1f2328;
    line-height: 1.6;
    margin-bottom: 16px;
}

.ok-box {
    background: rgba(26,127,55,0.08);
    border: 1px solid rgba(26,127,55,0.25);
    border-left: 4px solid #1a7f37;
    border-radius: 10px;
    padding: 10px 14px;
    color: #0f5323;
    margin: 8px 0;
}

.err-box {
    background: rgba(207,34,46,0.08);
    border: 1px solid rgba(207,34,46,0.25);
    border-left: 4px solid #cf222e;
    border-radius: 10px;
    padding: 10px 14px;
    color: #82071e;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# 도시 모델
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
    welfare, education, energy_infra, general_infra, safety,
    solar, hydrogen, ess, external
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
    welfare, education, energy_infra, general_infra, safety,
    solar, hydrogen, ess, external
):
    result, err = run_simulation_from_classes(
        welfare, education, energy_infra, general_infra, safety,
        solar, hydrogen, ess, external
    )

    if result is not None:
        scores = {key: float(result["districts"][key]) for key in DISTRICT_KEYS}
        return {
            "scores": scores,
            "average": float(result["city_average"]),
            "independence": float(result["independence_rate"]),
            "savings": float(result["savings"]),
            "warnings": result.get("warnings", []),
            "source": "classes.py OOP 모델",
        }

    energy_rate = expected_energy_self_rate(solar, hydrogen, ess, external)
    energy_bonus = (energy_rate - 0.4) * 18

    scores = {
        "A구역(산업단지)": (
            42 + general_infra * 0.30 + energy_infra * 0.18 + safety * 0.15
            + education * 0.08 + welfare * 0.05 + energy_bonus
        ),
        "B구역(대학가)": (
            40 + education * 0.33 + general_infra * 0.14 + safety * 0.08
            + energy_infra * 0.08 + welfare * 0.05 + energy_bonus
        ),
        "C구역(복지타운)": (
            38 + welfare * 0.38 + safety * 0.18 + general_infra * 0.08
            + education * 0.05 + energy_infra * 0.05 + energy_bonus
        ),
        "D구역(신도시)": (
            43 + welfare * 0.16 + education * 0.16 + energy_infra * 0.16
            + general_infra * 0.18 + safety * 0.14 + energy_bonus
        ),
        "E구역(구도심)": (
            36 + welfare * 0.22 + safety * 0.22 + general_infra * 0.20
            + education * 0.06 + energy_infra * 0.07 + energy_bonus
        ),
    }

    scores = {k: max(30, min(95, v)) for k, v in scores.items()}
    average = sum(scores.values()) / len(scores)
    warnings = [k for k, v in scores.items() if v < 50]

    return {
        "scores": scores,
        "average": average,
        "independence": energy_rate,
        "savings": max(0, energy_rate - 0.4) * 0.05,
        "warnings": warnings,
        "source": f"보조 계산 모델 · 실제 모델 오류: {err}",
    }


# ==================================================
# 유틸
# ==================================================
def clamp(value, low, high):
    return max(low, min(high, value))


def item_level(value):
    if value >= 35:
        return "S"
    if value >= 25:
        return "A"
    if value >= 15:
        return "B"
    if value > 0:
        return "C"
    return "-"


def item_slots(value, max_slots=5):
    return clamp(round(value / 20), 0, max_slots)


def score_face(score):
    if score < 50:
        return "😟"
    if score < 60:
        return "😐"
    if score < 75:
        return "🙂"
    return "😄"


def score_label(score):
    if score < 50:
        return "주의"
    if score < 60:
        return "보통"
    if score < 75:
        return "만족"
    return "매우 만족"


def score_color(score):
    if score < 50:
        return "#cf222e"
    if score < 60:
        return "#b07a12"
    if score < 75:
        return "#2b6de0"
    return "#1a7f37"


def score_stars(score):
    if score < 45:
        return "★☆☆☆☆"
    if score < 55:
        return "★★☆☆☆"
    if score < 70:
        return "★★★☆☆"
    if score < 82:
        return "★★★★☆"
    return "★★★★★"


def get_budget_values(welfare, education, energy_infra, general_infra, safety):
    return {
        "welfare": welfare,
        "education": education,
        "energy_infra": energy_infra,
        "general_infra": general_infra,
        "safety": safety,
    }


def get_energy_values(solar, hydrogen, ess, external):
    return {
        "solar": solar,
        "hydrogen": hydrogen,
        "ess": ess,
        "external": external,
    }


def get_top_budget_items_for_district(district_key, budget_values):
    weights = DISTRICT_INFO[district_key]["weights"]

    weighted = []
    for key, value in budget_values.items():
        weighted.append((key, value, value * weights[key]))

    weighted.sort(key=lambda x: x[2], reverse=True)
    return weighted[:3]


def get_facilities_for_district(district_key, budget_values):
    weights = DISTRICT_INFO[district_key]["weights"]

    weighted_items = []
    for key, value in budget_values.items():
        item = BUDGET_ITEMS[key]
        count = clamp(round((value * weights[key]) / 20), 1, 3)
        for _ in range(count):
            weighted_items.append((key, item["object"], item["name"], value * weights[key]))

    weighted_items.sort(key=lambda x: x[3], reverse=True)
    return weighted_items[:8]


def resident_emojis_for_district(district_key, score):
    info = DISTRICT_INFO[district_key]

    if score < 50:
        mood = "😟"
    elif score < 60:
        mood = "😐"
    elif score < 75:
        mood = "🙂"
    else:
        mood = "😄"

    residents = []
    for i in range(10):
        person = info["people"][i % len(info["people"])]
        residents.append((person, mood))

    return residents


def get_dashboard_url_from_secrets():
    try:
        return st.secrets.get("DASHBOARD_URL", "")
    except Exception:
        return ""


def build_query_string(
    preset_choice,
    welfare, education, energy_infra, general_infra, safety,
    solar, hydrogen, ess, external
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


def make_dashboard_link(
    dashboard_url,
    preset_choice,
    welfare, education, energy_infra, general_infra, safety,
    solar, hydrogen, ess, external
):
    if not dashboard_url:
        return """
        <div class="dash-link-empty">
            2차 대시보드 URL을 입력하면 상세 분석 화면으로 바로 이동할 수 있습니다.
        </div>
        """

    query = build_query_string(
        preset_choice,
        welfare, education, energy_infra, general_infra, safety,
        solar, hydrogen, ess, external
    )

    separator = "&" if "?" in dashboard_url else "?"
    linked = f"{dashboard_url}{separator}{query}"
    escaped = html_lib.escape(linked, quote=True)

    return f"""
    <a class="dash-link-btn" href="{escaped}" target="_blank">
        📊 2차 상세 대시보드 열기
    </a>
    """


# ==================================================
# HTML 생성 함수
# ==================================================
def make_item_slot_html(value, color):
    filled = item_slots(value)
    html = ""
    for i in range(5):
        cls = "slot active" if i < filled else "slot"
        html += f'<span class="{cls}" style="--slot-color:{color};"></span>'
    return html


def make_budget_inventory_html(budget_values):
    html = ""
    for key, value in budget_values.items():
        item = BUDGET_ITEMS[key]
        level = item_level(value)
        slots = make_item_slot_html(value, item["color"])

        html += f"""
        <div class="inventory-card" style="--item-color:{item['color']};">
            <div class="item-main">
                <div class="item-orb">{item['icon']}</div>
                <div class="item-text">
                    <div class="item-name">{item['item']}</div>
                    <div class="item-type">{item['name']} 정책 아이템</div>
                </div>
                <div class="item-rank">Lv.{level}</div>
            </div>
            <div class="item-desc">{item['desc']}</div>
            <div class="item-bottom">
                <div class="item-percent">{value}%</div>
                <div class="item-slots">{slots}</div>
            </div>
        </div>
        """
    return html


def make_energy_inventory_html(energy_values):
    html = ""
    for key, value in energy_values.items():
        item = ENERGY_ITEMS[key]
        level = item_level(value)
        slots = make_item_slot_html(value, item["color"])

        html += f"""
        <div class="inventory-card energy-item" style="--item-color:{item['color']};">
            <div class="item-main">
                <div class="item-orb">{item['icon']}</div>
                <div class="item-text">
                    <div class="item-name">{item['item']}</div>
                    <div class="item-type">{item['name']} 에너지 아이템</div>
                </div>
                <div class="item-rank">Lv.{level}</div>
            </div>
            <div class="item-desc">{item['desc']}</div>
            <div class="item-bottom">
                <div class="item-percent">{value}%</div>
                <div class="item-slots">{slots}</div>
            </div>
        </div>
        """
    return html


def make_applied_item_html(district_key, budget_values):
    top_items = get_top_budget_items_for_district(district_key, budget_values)

    html = ""
    for key, value, weighted_value in top_items:
        item = BUDGET_ITEMS[key]
        power = clamp(round(weighted_value), 0, 100)
        html += f"""
        <div class="applied-item" style="--item-color:{item['color']};">
            <div class="applied-icon">{item['icon']}</div>
            <div class="applied-text">
                <div class="applied-name">{item['item']}</div>
                <div class="applied-sub">강도 {power}</div>
            </div>
        </div>
        """
    return html


def make_facility_html(district_key, budget_values):
    facilities = get_facilities_for_district(district_key, budget_values)

    html = ""
    for key, icon, name, _ in facilities:
        item = BUDGET_ITEMS[key]
        html += f"""
        <div class="facility-item" style="--item-color:{item['color']};">
            <div class="facility-emoji">{icon}</div>
            <div class="facility-caption">{name}</div>
        </div>
        """
    return html


def make_residents_html(district_key, score):
    residents = resident_emojis_for_district(district_key, score)

    html = ""
    for person, mood in residents:
        html += f"""
        <div class="resident-item">
            <div class="resident-person">{person}</div>
            <div class="resident-mood">{mood}</div>
        </div>
        """
    return html


def make_district_card_html(district_key, score, budget_values):
    info = DISTRICT_INFO[district_key]
    color = score_color(score)
    face = score_face(score)
    label = score_label(score)
    stars = score_stars(score)

    applied_items_html = make_applied_item_html(district_key, budget_values)
    facilities_html = make_facility_html(district_key, budget_values)
    residents_html = make_residents_html(district_key, score)

    return f"""
    <div class="district-card">
        <div class="district-header">
            <div class="district-icon">{info['icon']}</div>
            <div>
                <div class="district-title">{info['label']}</div>
                <div class="district-desc">{info['desc']}</div>
            </div>
        </div>

        <div class="applied-panel">
            <div class="panel-title">적용된 정책 아이템</div>
            <div class="applied-list">
                {applied_items_html}
            </div>
        </div>

        <div class="district-content-grid">
            <div class="content-box">
                <div class="content-title">도시 시설 오브젝트</div>
                <div class="facility-grid">
                    {facilities_html}
                </div>
            </div>

            <div class="content-box">
                <div class="content-title">마을 사람들</div>
                <div class="resident-grid">
                    {residents_html}
                </div>
            </div>
        </div>

        <div class="district-score-panel">
            <div class="score-face-big">{face}</div>
            <div class="score-center">
                <div class="score-top-row">
                    <span class="score-state">{label}</span>
                    <span class="score-stars">{stars}</span>
                </div>
                <div class="score-bar-bg">
                    <div class="score-bar-fill"
                         style="width:{score:.1f}%; background:{color};"></div>
                </div>
                <div class="score-sub">시민 만족도</div>
            </div>
            <div class="score-right" style="color:{color};">
                {score:.1f}
            </div>
        </div>
    </div>
    """


def make_energy_object_field_html(energy_values):
    html = ""
    for key, value in energy_values.items():
        item = ENERGY_ITEMS[key]
        count = clamp(round(value / 20), 0, 5)

        object_html = ""
        for _ in range(count):
            object_html += f"""
            <div class="energy-object" style="--item-color:{item['color']};">
                <div class="energy-object-icon">{item['object']}</div>
            </div>
            """

        if count == 0:
            object_html = """
            <div class="energy-empty">투입 없음</div>
            """

        html += f"""
        <div class="energy-field-card" style="--item-color:{item['color']};">
            <div class="energy-field-head">
                <div class="energy-field-icon">{item['icon']}</div>
                <div>
                    <div class="energy-field-name">{item['name']}</div>
                    <div class="energy-field-value">{value}%</div>
                </div>
            </div>
            <div class="energy-object-grid">
                {object_html}
            </div>
            <div class="energy-field-desc">{item['desc']}</div>
        </div>
        """
    return html


def make_main_scene_html(
    preset_choice,
    welfare, education, energy_infra, general_infra, safety,
    solar, hydrogen, ess, external,
    result,
    dashboard_url
):
    budget_values = get_budget_values(welfare, education, energy_infra, general_infra, safety)
    energy_values = get_energy_values(solar, hydrogen, ess, external)

    avg = result["average"]
    independence = result["independence"]
    warnings = result["warnings"]
    savings = result["savings"]
    source = result["source"]

    district_cards = ""
    for key in DISTRICT_KEYS:
        district_cards += make_district_card_html(
            key,
            result["scores"][key],
            budget_values
        )

    budget_inventory = make_budget_inventory_html(budget_values)
    energy_inventory = make_energy_inventory_html(energy_values)
    energy_objects = make_energy_object_field_html(energy_values)

    dashboard_button = make_dashboard_link(
        dashboard_url,
        preset_choice,
        welfare, education, energy_infra, general_infra, safety,
        solar, hydrogen, ess, external
    )

    warning_text = "위험 구역 없음" if not warnings else f"주의 구역 {len(warnings)}개"
    warning_color = "#1a7f37" if not warnings else "#cf222e"

    html = f"""
    <style>
    * {{
        box-sizing: border-box;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    body {{
        margin: 0;
        background: #f7f8fb;
    }}

    .root {{
        width: 100%;
        padding: 10px 8px 32px;
        color: #1f2328;
    }}

    .hero {{
        background:
            linear-gradient(135deg, #26364f 0%, #315f80 52%, #4b8f9f 100%);
        border-radius: 28px;
        padding: 28px 30px;
        color: white;
        position: relative;
        overflow: hidden;
        box-shadow: 0 18px 34px rgba(38,54,79,0.22);
        margin-bottom: 18px;
    }}

    .hero-content {{
        position: relative;
        z-index: 2;
        display: grid;
        grid-template-columns: 1.5fr 1fr;
        gap: 18px;
        align-items: center;
    }}

    .hero-eyebrow {{
        font-size: 13px;
        font-weight: 900;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        opacity: 0.9;
        margin-bottom: 8px;
    }}

    .hero-title {{
        font-size: 38px;
        font-weight: 900;
        line-height: 1.22;
        margin-bottom: 10px;
    }}

    .hero-desc {{
        font-size: 16px;
        line-height: 1.75;
        opacity: 0.96;
    }}

    .hero-panel {{
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.24);
        border-radius: 22px;
        padding: 16px 18px;
        backdrop-filter: blur(4px);
    }}

    .hero-stat {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.16);
    }}

    .hero-stat:last-child {{
        border-bottom: none;
    }}

    .hero-stat-name {{
        font-size: 13px;
        font-weight: 800;
    }}

    .hero-stat-value {{
        font-size: 18px;
        font-weight: 900;
    }}

    .hud-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 18px;
    }}

    .hud-card {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 22px;
        padding: 18px 20px;
        min-height: 116px;
        box-shadow: 0 10px 20px rgba(27,31,36,0.06);
    }}

    .hud-label {{
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #656d76;
        margin-bottom: 8px;
    }}

    .hud-value {{
        font-size: 30px;
        font-weight: 900;
        color: #0969da;
        line-height: 1.05;
    }}

    .hud-sub {{
        font-size: 13px;
        color: #57606a;
        line-height: 1.55;
        margin-top: 8px;
    }}

    .section-title {{
        font-size: 24px;
        font-weight: 900;
        margin-bottom: 6px;
        color: #1f2328;
    }}

    .section-sub {{
        font-size: 14px;
        color: #57606a;
        line-height: 1.65;
        margin-bottom: 14px;
    }}

    .inventory-grid {{
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 22px;
    }}

    .inventory-grid.energy {{
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }}

    .inventory-card {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-top: 4px solid var(--item-color);
        border-radius: 20px;
        padding: 14px;
        box-shadow: 0 10px 18px rgba(27,31,36,0.06);
        position: relative;
        overflow: hidden;
    }}

    .item-main {{
        display: grid;
        grid-template-columns: 48px 1fr 50px;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }}

    .item-orb {{
        width: 48px;
        height: 48px;
        border-radius: 17px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 27px;
        box-shadow: 0 8px 16px rgba(27,31,36,0.13);
    }}

    .item-name {{
        font-size: 15px;
        font-weight: 900;
        color: #1f2328;
        margin-bottom: 2px;
    }}

    .item-type {{
        font-size: 11px;
        color: #57606a;
        line-height: 1.35;
    }}

    .item-rank {{
        background: var(--item-color);
        color: white;
        border-radius: 999px;
        padding: 5px 8px;
        font-size: 11px;
        font-weight: 900;
        text-align: center;
    }}

    .item-desc {{
        font-size: 12px;
        color: #57606a;
        line-height: 1.5;
        min-height: 38px;
        margin-bottom: 10px;
    }}

    .item-bottom {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
    }}

    .item-percent {{
        font-size: 22px;
        font-weight: 900;
        color: var(--item-color);
    }}

    .item-slots {{
        display: flex;
        gap: 4px;
    }}

    .slot {{
        width: 12px;
        height: 12px;
        border-radius: 4px;
        background: #e5e7eb;
    }}

    .slot.active {{
        background: var(--slot-color);
    }}

    .simulation-board {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 28px;
        padding: 22px;
        box-shadow: 0 14px 28px rgba(27,31,36,0.07);
        margin-bottom: 24px;
    }}

    .district-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
    }}

    .district-card {{
        background:
            linear-gradient(180deg, rgba(255,255,255,0.96), rgba(250,252,255,0.96));
        border: 1px solid #d0d7de;
        border-radius: 26px;
        padding: 18px;
        box-shadow: 0 10px 24px rgba(27,31,36,0.06);
        min-height: 520px;
        overflow: hidden;
    }}

    .district-header {{
        display: grid;
        grid-template-columns: 58px 1fr;
        gap: 12px;
        align-items: center;
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 20px;
        padding: 12px 14px;
        margin-bottom: 14px;
    }}

    .district-icon {{
        width: 50px;
        height: 50px;
        border-radius: 17px;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        border: 1px solid #e5e7eb;
    }}

    .district-title {{
        font-size: 18px;
        font-weight: 900;
        color: #1f2328;
        margin-bottom: 3px;
    }}

    .district-desc {{
        font-size: 13px;
        color: #57606a;
        line-height: 1.4;
    }}

    .applied-panel {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 12px;
        margin-bottom: 14px;
    }}

    .panel-title {{
        font-size: 12px;
        font-weight: 900;
        color: #57606a;
        margin-bottom: 8px;
    }}

    .applied-list {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
    }}

    .applied-item {{
        display: grid;
        grid-template-columns: 34px 1fr;
        align-items: center;
        gap: 8px;
        background: #f6f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 8px;
        min-width: 0;
    }}

    .applied-icon {{
        width: 32px;
        height: 32px;
        border-radius: 11px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }}

    .applied-name {{
        font-size: 12px;
        font-weight: 900;
        color: #1f2328;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .applied-sub {{
        font-size: 10px;
        color: #6b7280;
    }}

    .district-content-grid {{
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 14px;
        margin-bottom: 14px;
    }}

    .content-box {{
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 12px;
        min-height: 214px;
    }}

    .content-title {{
        font-size: 12px;
        color: #57606a;
        font-weight: 900;
        margin-bottom: 10px;
    }}

    .facility-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
    }}

    .facility-item {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 8px 6px;
        text-align: center;
        min-height: 76px;
    }}

    .facility-emoji {{
        width: 38px;
        height: 38px;
        margin: 0 auto 5px;
        border-radius: 13px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 23px;
        box-shadow: 0 6px 12px rgba(27,31,36,0.10);
    }}

    .facility-caption {{
        font-size: 10px;
        font-weight: 800;
        color: #374151;
    }}

    .resident-grid {{
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 10px;
    }}

    .resident-item {{
        position: relative;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        height: 62px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .resident-person {{
        font-size: 30px;
    }}

    .resident-mood {{
        position: absolute;
        right: -4px;
        top: -5px;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: #ffffff;
        border: 2px solid #d0d7de;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        box-shadow: 0 4px 8px rgba(27,31,36,0.12);
    }}

    .district-score-panel {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 20px;
        display: grid;
        grid-template-columns: 58px 1fr 76px;
        gap: 12px;
        align-items: center;
        padding: 14px;
        box-shadow: 0 8px 16px rgba(27,31,36,0.05);
    }}

    .score-face-big {{
        width: 50px;
        height: 50px;
        border-radius: 17px;
        background: #fff7ed;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 29px;
    }}

    .score-top-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 7px;
        gap: 10px;
    }}

    .score-state {{
        font-size: 15px;
        font-weight: 900;
        color: #1f2328;
    }}

    .score-stars {{
        font-size: 14px;
        color: #f59e0b;
        font-weight: 800;
    }}

    .score-bar-bg {{
        height: 11px;
        border-radius: 999px;
        background: #e5e7eb;
        overflow: hidden;
    }}

    .score-bar-fill {{
        height: 100%;
        border-radius: 999px;
    }}

    .score-sub {{
        font-size: 12px;
        color: #6b7280;
        margin-top: 5px;
    }}

    .score-right {{
        font-size: 36px;
        font-weight: 900;
        text-align: right;
        line-height: 1;
    }}

    .energy-section {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 28px;
        padding: 22px;
        box-shadow: 0 14px 28px rgba(27,31,36,0.07);
        margin-bottom: 24px;
    }}

    .energy-object-grid-section {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
    }}

    .energy-field-card {{
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-top: 4px solid var(--item-color);
        border-radius: 20px;
        padding: 14px;
        min-height: 220px;
    }}

    .energy-field-head {{
        display: grid;
        grid-template-columns: 44px 1fr;
        gap: 10px;
        align-items: center;
        margin-bottom: 12px;
    }}

    .energy-field-icon {{
        width: 42px;
        height: 42px;
        border-radius: 15px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }}

    .energy-field-name {{
        font-size: 15px;
        font-weight: 900;
        color: #1f2328;
    }}

    .energy-field-value {{
        font-size: 13px;
        color: var(--item-color);
        font-weight: 900;
    }}

    .energy-object-grid {{
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 8px;
        min-height: 94px;
        margin-bottom: 10px;
    }}

    .energy-object {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        height: 46px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .energy-object-icon {{
        width: 34px;
        height: 34px;
        border-radius: 12px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 21px;
    }}

    .energy-empty {{
        grid-column: 1 / -1;
        color: #8c959f;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 90px;
        border: 1px dashed #d0d7de;
        border-radius: 14px;
        background: #ffffff;
    }}

    .energy-field-desc {{
        font-size: 12px;
        color: #57606a;
        line-height: 1.5;
    }}

    .reaction-box {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 24px;
        padding: 20px 22px;
        box-shadow: 0 10px 22px rgba(27,31,36,0.06);
        margin-bottom: 18px;
    }}

    .reaction-title {{
        font-size: 22px;
        font-weight: 900;
        color: #1f2328;
        margin-bottom: 8px;
    }}

    .reaction-desc {{
        font-size: 15px;
        color: #57606a;
        line-height: 1.75;
    }}

    .final-card {{
        background: linear-gradient(135deg, #f0fff4 0%, #ddf4ff 100%);
        border: 1px solid #aceebb;
        border-radius: 26px;
        padding: 24px 26px;
        box-shadow: 0 12px 24px rgba(27,31,36,0.06);
        margin-top: 10px;
    }}

    .final-title {{
        font-size: 26px;
        font-weight: 900;
        margin-bottom: 8px;
        color: #1f2328;
    }}

    .final-desc {{
        font-size: 15px;
        line-height: 1.75;
        color: #57606a;
        margin-bottom: 16px;
    }}

    .dash-link-btn {{
        display: inline-block;
        background: #0969da;
        color: white !important;
        text-decoration: none !important;
        padding: 12px 18px;
        border-radius: 14px;
        font-size: 14px;
        font-weight: 900;
        box-shadow: 0 8px 16px rgba(9,105,218,0.18);
    }}

    .dash-link-empty {{
        display: inline-block;
        background: rgba(255,255,255,0.78);
        border: 1px solid #d0d7de;
        border-radius: 14px;
        padding: 12px 14px;
        font-size: 13px;
        color: #57606a;
    }}

    .mini-note {{
        margin-top: 10px;
        font-size: 11px;
        color: #8c959f;
        line-height: 1.5;
    }}

    @media (max-width: 1100px) {{
        .hero-content,
        .hud-grid,
        .inventory-grid,
        .inventory-grid.energy,
        .district-grid,
        .district-content-grid,
        .energy-object-grid-section {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>

    <div class="root">
        <div class="hero">
            <div class="hero-content">
                <div>
                    <div class="hero-eyebrow">NOVA Smart City Item Simulation</div>
                    <div class="hero-title">겹침 없이 정돈된 아이템형 스마트시티 시뮬레이션</div>
                    <div class="hero-desc">
                        배경 장식과 겹치는 오브젝트를 제거하고, 정책 아이템·시설·주민·만족도를
                        구역별 카드 안에서 명확하게 확인할 수 있도록 재구성했습니다.
                    </div>
                </div>

                <div class="hero-panel">
                    <div class="hero-stat">
                        <div class="hero-stat-name">현재 시나리오</div>
                        <div class="hero-stat-value">{html_lib.escape(preset_choice)}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-name">도시 평균 만족도</div>
                        <div class="hero-stat-value">{avg:.1f}점</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-name">에너지 자립률</div>
                        <div class="hero-stat-value">{independence * 100:.1f}%</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-name">도시 상태</div>
                        <div class="hero-stat-value" style="color:{warning_color};">{warning_text}</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="hud-grid">
            <div class="hud-card">
                <div class="hud-label">선택 정책</div>
                <div class="hud-value" style="font-size:24px;">{html_lib.escape(preset_choice)}</div>
                <div class="hud-sub">정책 아이템과 구역별 적용 결과가 함께 표시됩니다.</div>
            </div>

            <div class="hud-card">
                <div class="hud-label">시민 만족도 평균</div>
                <div class="hud-value">{avg:.1f}점</div>
                <div class="hud-sub">구역별 주민 구성과 정책 아이템 효과가 반영됩니다.</div>
            </div>

            <div class="hud-card">
                <div class="hud-label">에너지 자립률</div>
                <div class="hud-value">{independence * 100:.1f}%</div>
                <div class="hud-sub">에너지 아이템 조합에 따라 자립률이 달라집니다.</div>
            </div>

            <div class="hud-card">
                <div class="hud-label">절감액 환원 효과</div>
                <div class="hud-value">{savings * 100:.2f}%</div>
                <div class="hud-sub">{html_lib.escape(source)}</div>
            </div>
        </div>

        <div class="section-title">🎒 정책 아이템 인벤토리</div>
        <div class="section-sub">
            내가 처치한 예산 배분을 게임 아이템처럼 표현했습니다. 비율이 높을수록 아이템 레벨과 슬롯이 커집니다.
        </div>
        <div class="inventory-grid">
            {budget_inventory}
        </div>

        <div class="section-title">⚡ 에너지 아이템 인벤토리</div>
        <div class="section-sub">
            에너지 배분도 아이템 오브젝트로 표현했습니다. 태양광, 수소, ESS, 외부전력망의 구성이 자립률을 결정합니다.
        </div>
        <div class="inventory-grid energy">
            {energy_inventory}
        </div>

        <div class="simulation-board">
            <div class="section-title">🏘️ 구역별 정책 적용 시뮬레이션</div>
            <div class="section-sub">
                구역 카드끼리 겹치지 않도록 그리드 구조로 재배치했습니다.
                각 구역 안에서 적용된 정책 아이템, 시설 오브젝트, 주민 반응, 만족도를 순서대로 볼 수 있습니다.
            </div>
            <div class="district-grid">
                {district_cards}
            </div>
        </div>

        <div class="energy-section">
            <div class="section-title">⚡ 에너지 아이템 필드</div>
            <div class="section-sub">
                에너지 오브젝트가 지도 위에 겹치지 않도록 별도 필드로 분리했습니다.
                투입 비율에 따라 각 에너지 오브젝트 개수가 달라집니다.
            </div>
            <div class="energy-object-grid-section">
                {energy_objects}
            </div>
        </div>

        <div class="reaction-box">
            <div class="reaction-title">🗣️ 마을 사람들의 반응</div>
            <div class="reaction-desc">
                “이제 어떤 정책 아이템이 우리 구역에 들어왔는지 더 잘 보여요.
                시설과 주민, 만족도가 분리되어 보여서 정책 처치의 결과를 한눈에 이해할 수 있어요.”
            </div>
        </div>

        <div class="final-card">
            <div class="final-title">📊 다음 단계: 정량 분석 대시보드로 이동</div>
            <div class="final-desc">
                지금 화면은 정책 처치가 마을의 모습과 주민 상태를 어떻게 바꾸는지를 시각적으로 보여주는 1차 시뮬레이션입니다.
                다음 단계에서는 같은 입력값을 기반으로 2차 대시보드에서 구역별 만족도, 평균 점수,
                에너지 자립률, 시나리오 비교를 정량적으로 분석할 수 있습니다.
            </div>
            {dashboard_button}
            <div class="mini-note">
                이 버전은 겹침을 줄이기 위해 기존 absolute map 구조를 제거하고, 카드형 그리드 구조로 재설계했습니다.
            </div>
        </div>
    </div>
    """

    return html


# ==================================================
# 사이드바
# ==================================================
with st.sidebar:
    st.markdown("## 🎮 NOVA시 아이템 시뮬레이터")
    st.caption("예산과 에너지를 게임 아이템처럼 투입해 마을 변화를 확인합니다.")

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
        st.markdown(f'<div class="ok-box">예산 합계: {budget_total}% ✓</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="err-box">예산 합계: {budget_total}% · 정확히 100% 필요</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚡ 에너지 배분")

    solar = st.slider("태양광", 0, 100, pv("solar", 40), 1, key=f"sol_{preset_key}")
    hydrogen = st.slider("수소연료전지", 0, 100, pv("hydrogen", 35), 1, key=f"hyd_{preset_key}")
    ess = st.slider("ESS", 0, 100, pv("ess", 20), 1, key=f"ess_{preset_key}")
    external = st.slider("외부전력망", 0, 100, pv("external", 5), 1, key=f"ext_{preset_key}")

    energy_total = solar + hydrogen + ess + external
    energy_ok = energy_total == 100

    if energy_ok:
        st.markdown(f'<div class="ok-box">에너지 합계: {energy_total}% ✓</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="err-box">에너지 합계: {energy_total}% · 정확히 100% 필요</div>', unsafe_allow_html=True)

    predicted_rate = expected_energy_self_rate(solar, hydrogen, ess, external)
    st.info(
        f"예상 에너지 자립률: {predicted_rate * 100:.1f}%\n\n"
        "계산식: 태양광×0.7 + 수소연료전지×0.9 + ESS×0.6 + 외부전력망×0.0"
    )

    st.markdown("---")

    default_dashboard_url = get_dashboard_url_from_secrets()
    dashboard_url = st.text_input(
        "2차 대시보드 URL",
        value=default_dashboard_url,
        placeholder="예: https://your-dashboard.streamlit.app",
    )
    st.caption("기존 dashboard.py 앱 URL을 입력하면 결과를 바로 넘길 수 있습니다.")


# ==================================================
# 메인
# ==================================================
st.markdown("""
<div class="app-title">🎮 NOVA시 아이템형 스마트시티 시뮬레이션</div>
<div class="app-subtitle">
겹치는 지도형 화면을 정리하고, 예산·에너지 처치를 아이템 인벤토리와 구역별 카드로 명확하게 시각화했습니다.
</div>
""", unsafe_allow_html=True)

if not HAS_CLASSES:
    st.warning(
        "classes.py를 불러오지 못했습니다. 보조 계산으로 시뮬레이션 화면은 표시됩니다. "
        f"오류: {IMPORT_ERROR_MESSAGE}"
    )

st.markdown("""
<div class="box-warn">
<b>이번 수정의 핵심</b><br>
- 구역 카드, 시설, 주민, 만족도가 서로 겹치지 않도록 그리드 구조로 변경<br>
- 배경의 구름, 산, 숲, 큰 도로 등 시선 분산 요소 제거<br>
- 에너지 아이템 필드를 지도에서 분리해 별도 섹션으로 정리<br>
- 각 구역에서 적용된 정책 아이템과 시민 반응이 더 명확하게 보이도록 개선
</div>
""", unsafe_allow_html=True)

if not budget_ok or not energy_ok:
    st.markdown("""
    <div class="box-info">
        <b>시뮬레이션 실행 조건</b><br>
        예산 합계와 에너지 합계가 각각 정확히 100%가 되도록 조정해야
        도시 장면이 정상적으로 그려집니다.
    </div>
    """, unsafe_allow_html=True)
    st.stop()


result = run_model_or_fallback(
    welfare, education, energy_infra, general_infra, safety,
    solar, hydrogen, ess, external
)

scene_html = make_main_scene_html(
    preset_choice,
    welfare, education, energy_infra, general_infra, safety,
    solar, hydrogen, ess, external,
    result,
    dashboard_url
)

components.html(scene_html, height=2850, scrolling=True)

st.markdown("### 발표용 연결 멘트 예시")
st.markdown("""
이 1차 시뮬레이션은 예산과 에너지 배분을 아이템처럼 시각화해서, 내가 어떤 처치를 했고 그 처치가 어느 구역에 어떻게 적용되었는지 보여줍니다.  
이제 같은 입력값을 2차 대시보드에서 확인하면서, 실제 시민 만족도와 에너지 자립률을 정량적으로 분석하겠습니다.
""")
