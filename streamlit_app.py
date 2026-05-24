"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOVA시 마을형 스마트시티 정책 시뮬레이션
simulation_story.py

실행:
streamlit run simulation_story.py

requirements.txt:
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
    page_title="NOVA시 마을형 스마트시티 시뮬레이션",
    page_icon="🏘️",
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


# ==================================================
# 구역 정보
# 전체 화면이 너무 커지지 않도록 이전보다 축소
# 단, 내부 박스가 잘리지 않도록 높이는 충분히 확보
# ==================================================
DISTRICT_INFO = {
    "A구역(산업단지)": {
        "short": "A",
        "label": "A구역 산업단지",
        "icon": "🏭",
        "desc": "근로자 중심 · 이동성·에너지·인프라 민감",
        "x": 70,
        "y": 565,
        "w": 390,
        "h": 490,
        "people": ["👷", "👩‍🏭", "🧑‍💼", "👨‍🔧", "👩‍💼"],
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
        "icon": "🎓",
        "desc": "학생 중심 · 교육·문화·기회 민감",
        "x": 150,
        "y": 115,
        "w": 390,
        "h": 490,
        "people": ["🧑‍🎓", "👩‍🎓", "🧑‍💻", "👨‍🎓", "👩‍💻"],
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
        "icon": "🏥",
        "desc": "노인·취약계층 중심 · 복지·안전 민감",
        "x": 805,
        "y": 115,
        "w": 390,
        "h": 490,
        "people": ["👵", "👴", "👩‍⚕️", "🧓", "👨‍⚕️"],
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
        "icon": "🏙️",
        "desc": "혼합형 시민 구성 · 균형 정책 반응",
        "x": 470,
        "y": 660,
        "w": 390,
        "h": 490,
        "people": ["👨‍👩‍👧", "🧑‍💼", "👩‍💻", "🧑", "👨‍👩‍👦"],
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
        "icon": "🏘️",
        "desc": "노후 인프라 · 복지·안전·생활SOC 민감",
        "x": 870,
        "y": 635,
        "w": 390,
        "h": 490,
        "people": ["🧑", "👵", "👴", "👨‍👩‍👧", "👩"],
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
# 아이템 정의
# ==================================================
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
# Streamlit 기본 CSS
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
# 유틸 함수
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


def satisfaction_comment(district_key, score, budget_values):
    top_key = max(budget_values, key=budget_values.get)
    top_item = BUDGET_ITEMS[top_key]["name"]

    if score < 50:
        tone = "아직 생활이 불편해요"
        detail = "우리 구역에 필요한 시설이 더 필요해 보여요."
    elif score < 60:
        tone = "조금 나아졌지만 아쉬워요"
        detail = f"{top_item} 투입 효과는 보이지만 아직 체감은 제한적이에요."
    elif score < 75:
        tone = "살기 좋아지고 있어요"
        detail = f"{top_item} 중심의 정책이 생활환경 개선으로 이어지고 있어요."
    else:
        tone = "정말 만족스러워요"
        detail = "필요한 시설과 서비스가 균형 있게 들어와서 체감 만족도가 높아요."

    return tone, detail


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
        count = clamp(round((value * weights[key]) / 24), 1, 3)

        for _ in range(count):
            weighted_items.append((key, item["object"], item["name"], value * weights[key]))

    weighted_items.sort(key=lambda x: x[3], reverse=True)
    return weighted_items[:6]


def get_residents_for_district(district_key, score):
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
    for i in range(8):
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
    residents = get_residents_for_district(district_key, score)

    html = ""

    for person, mood in residents:
        html += f"""
        <div class="resident-item">
            <div class="resident-person">{person}</div>
            <div class="resident-mood">{mood}</div>
        </div>
        """

    return html


def make_district_zone_html(district_key, score, budget_values):
    info = DISTRICT_INFO[district_key]
    color = score_color(score)
    face = score_face(score)
    label = score_label(score)
    stars = score_stars(score)
    tone, detail = satisfaction_comment(district_key, score, budget_values)

    applied_items_html = make_applied_item_html(district_key, budget_values)
    facilities_html = make_facility_html(district_key, budget_values)
    residents_html = make_residents_html(district_key, score)

    return f"""
    <div class="district-zone"
         style="left:{info['x']}px; top:{info['y']}px; width:{info['w']}px; height:{info['h']}px;">

        <div class="district-header">
            <div class="district-icon">{info['icon']}</div>
            <div>
                <div class="district-title">{info['label']}</div>
                <div class="district-desc">{info['desc']}</div>
            </div>
        </div>

        <div class="applied-panel">
            <div class="applied-title">적용된 정책 아이템</div>
            <div class="applied-list">
                {applied_items_html}
            </div>
        </div>

        <div class="district-scene">
            <div class="scene-road scene-road-a"></div>
            <div class="scene-road scene-road-b"></div>

            <div class="scene-section facility-section">
                <div class="scene-label">시설 변화</div>
                <div class="facility-grid">
                    {facilities_html}
                </div>
            </div>

            <div class="scene-section resident-section">
                <div class="scene-label">주민 반응</div>
                <div class="resident-grid">
                    {residents_html}
                </div>
            </div>
        </div>

        <div class="comment-bubble">
            <div class="comment-title">{tone}</div>
            <div class="comment-text">{detail}</div>
        </div>

        <div class="district-score">
            <div class="score-face">{face}</div>
            <div class="score-center">
                <div class="score-row">
                    <span class="score-state">{label}</span>
                    <span class="score-stars">{stars}</span>
                </div>
                <div class="score-bar">
                    <div class="score-fill" style="width:{score:.1f}%; background:{color};"></div>
                </div>
            </div>
            <div class="score-num" style="color:{color};">{score:.1f}</div>
        </div>
    </div>
    """


def make_energy_field_html(energy_values):
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
            object_html = '<div class="energy-empty">투입 없음</div>'

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

    district_zones = ""
    for key in DISTRICT_KEYS:
        district_zones += make_district_zone_html(
            key,
            result["scores"][key],
            budget_values
        )

    budget_inventory = make_budget_inventory_html(budget_values)
    energy_inventory = make_energy_inventory_html(energy_values)
    energy_field = make_energy_field_html(energy_values)

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
        padding: 8px 6px 28px;
        color: #1f2328;
    }}

    .hero {{
        background: linear-gradient(135deg, #26364f 0%, #315f80 52%, #4b8f9f 100%);
        border-radius: 24px;
        padding: 24px 28px;
        color: white;
        overflow: hidden;
        box-shadow: 0 14px 28px rgba(38,54,79,0.20);
        margin-bottom: 16px;
    }}

    .hero-content {{
        display: grid;
        grid-template-columns: 1.5fr 1fr;
        gap: 18px;
        align-items: center;
    }}

    .hero-eyebrow {{
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        opacity: 0.9;
        margin-bottom: 8px;
    }}

    .hero-title {{
        font-size: 34px;
        font-weight: 900;
        line-height: 1.22;
        margin-bottom: 10px;
    }}

    .hero-desc {{
        font-size: 15px;
        line-height: 1.7;
        opacity: 0.96;
    }}

    .hero-panel {{
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.24);
        border-radius: 20px;
        padding: 14px 16px;
        backdrop-filter: blur(4px);
    }}

    .hero-stat {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 9px 0;
        border-bottom: 1px solid rgba(255,255,255,0.16);
    }}

    .hero-stat:last-child {{
        border-bottom: none;
    }}

    .hero-stat-name {{
        font-size: 12px;
        font-weight: 800;
    }}

    .hero-stat-value {{
        font-size: 17px;
        font-weight: 900;
    }}

    .hud-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 18px;
    }}

    .hud-card {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 20px;
        padding: 16px 18px;
        min-height: 105px;
        box-shadow: 0 8px 18px rgba(27,31,36,0.05);
    }}

    .hud-label {{
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #656d76;
        margin-bottom: 8px;
    }}

    .hud-value {{
        font-size: 27px;
        font-weight: 900;
        color: #0969da;
        line-height: 1.05;
    }}

    .hud-sub {{
        font-size: 12px;
        color: #57606a;
        line-height: 1.5;
        margin-top: 8px;
    }}

    .section-title {{
        font-size: 22px;
        font-weight: 900;
        margin-bottom: 6px;
        color: #1f2328;
    }}

    .section-sub {{
        font-size: 13px;
        color: #57606a;
        line-height: 1.6;
        margin-bottom: 12px;
    }}

    .inventory-grid {{
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 10px;
        margin-bottom: 20px;
    }}

    .inventory-grid.energy {{
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }}

    .inventory-card {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-top: 4px solid var(--item-color);
        border-radius: 18px;
        padding: 12px;
        box-shadow: 0 8px 16px rgba(27,31,36,0.05);
    }}

    .item-main {{
        display: grid;
        grid-template-columns: 42px 1fr 46px;
        align-items: center;
        gap: 8px;
        margin-bottom: 9px;
    }}

    .item-orb {{
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

    .item-name {{
        font-size: 14px;
        font-weight: 900;
        color: #1f2328;
        margin-bottom: 2px;
    }}

    .item-type {{
        font-size: 10.5px;
        color: #57606a;
        line-height: 1.3;
    }}

    .item-rank {{
        background: var(--item-color);
        color: white;
        border-radius: 999px;
        padding: 5px 7px;
        font-size: 10px;
        font-weight: 900;
        text-align: center;
    }}

    .item-desc {{
        font-size: 11px;
        color: #57606a;
        line-height: 1.45;
        min-height: 34px;
        margin-bottom: 8px;
    }}

    .item-bottom {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
    }}

    .item-percent {{
        font-size: 20px;
        font-weight: 900;
        color: var(--item-color);
    }}

    .item-slots {{
        display: flex;
        gap: 4px;
    }}

    .slot {{
        width: 11px;
        height: 11px;
        border-radius: 4px;
        background: #e5e7eb;
    }}

    .slot.active {{
        background: var(--slot-color);
    }}

    .village-scroll {{
        width: 100%;
        overflow-x: auto;
        padding-bottom: 10px;
        margin-bottom: 22px;
    }}

    .village-board {{
        position: relative;
        width: 1320px;
        height: 1180px;
        border-radius: 30px;
        overflow: hidden;
        border: 1px solid #d0d7de;
        background:
            linear-gradient(180deg, #eaf5ff 0%, #eef8ff 22%, #edf7e6 55%, #dfeccd 100%);
        box-shadow: 0 16px 30px rgba(27,31,36,0.08);
    }}

    .village-title-card {{
        position: absolute;
        left: 24px;
        top: 24px;
        width: 330px;
        background: rgba(255,255,255,0.94);
        border: 1px solid #d0d7de;
        border-radius: 20px;
        padding: 14px 16px;
        box-shadow: 0 8px 18px rgba(27,31,36,0.07);
        z-index: 20;
    }}

    .village-title {{
        font-size: 21px;
        font-weight: 900;
        color: #1f2328;
        margin-bottom: 4px;
    }}

    .village-desc {{
        font-size: 12px;
        line-height: 1.5;
        color: #57606a;
    }}

    .main-road {{
        position: absolute;
        background: #7b8491;
        box-shadow: inset 0 0 0 2px rgba(255,255,255,0.15);
        z-index: 1;
    }}

    .main-road::after {{
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        width: 1600px;
        border-top: 3px dashed rgba(255,255,255,0.72);
    }}

    .road-1 {{
        left: -100px;
        top: 570px;
        width: 1600px;
        height: 42px;
        transform: rotate(-7deg);
    }}

    .road-2 {{
        left: 440px;
        top: -80px;
        width: 50px;
        height: 1400px;
        transform: rotate(10deg);
    }}

    .road-3 {{
        left: 880px;
        top: -80px;
        width: 50px;
        height: 1400px;
        transform: rotate(-12deg);
    }}

    .water-line {{
        position: absolute;
        left: -80px;
        bottom: 24px;
        width: 1550px;
        height: 70px;
        transform: rotate(-5deg);
        background:
            repeating-linear-gradient(
                120deg,
                rgba(255,255,255,0.32) 0 12px,
                rgba(255,255,255,0.08) 12px 24px
            ),
            #8ec5ff;
        border-radius: 999px;
        z-index: 1;
    }}

    .district-zone {{
        position: absolute;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.36), rgba(255,255,255,0.20)),
            repeating-linear-gradient(45deg, #dcedc5 0 18px, #d7e8bf 18px 36px);
        border: 2px solid rgba(255,255,255,0.95);
        border-radius: 26px;
        box-shadow: 0 14px 26px rgba(27,31,36,0.12);
        overflow: hidden;
        z-index: 5;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }}

    .district-header {{
        min-height: 70px;
        background: rgba(255,255,255,0.98);
        border: 1px solid #d0d7de;
        border-radius: 20px;
        display: grid;
        grid-template-columns: 50px 1fr;
        gap: 10px;
        align-items: center;
        padding: 10px 12px;
        box-shadow: 0 6px 12px rgba(27,31,36,0.05);
        flex-shrink: 0;
    }}

    .district-icon {{
        width: 46px;
        height: 46px;
        border-radius: 16px;
        background: #f6f8fa;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
    }}

    .district-title {{
        font-size: 18px;
        font-weight: 900;
        color: #1f2328;
        margin-bottom: 3px;
        white-space: nowrap;
    }}

    .district-desc {{
        font-size: 12px;
        color: #57606a;
        line-height: 1.35;
        white-space: normal;
    }}

    .applied-panel {{
        min-height: 76px;
        background: rgba(255,255,255,0.96);
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 9px 10px;
        box-shadow: 0 5px 10px rgba(27,31,36,0.05);
        flex-shrink: 0;
    }}

    .applied-title {{
        font-size: 11.5px;
        font-weight: 900;
        color: #57606a;
        margin-bottom: 7px;
    }}

    .applied-list {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
    }}

    .applied-item {{
        display: grid;
        grid-template-columns: 30px 1fr;
        gap: 7px;
        align-items: center;
        min-width: 0;
        background: #f6f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 13px;
        padding: 6px 7px;
    }}

    .applied-icon {{
        width: 29px;
        height: 29px;
        border-radius: 10px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }}

    .applied-name {{
        font-size: 11px;
        font-weight: 900;
        color: #1f2328;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .applied-sub {{
        font-size: 9.5px;
        color: #6b7280;
    }}

    .district-scene {{
        position: relative;
        height: 128px;
        background: rgba(255,255,255,0.44);
        border: 1px solid rgba(255,255,255,0.78);
        border-radius: 18px;
        overflow: hidden;
        display: grid;
        grid-template-columns: 1.05fr 0.95fr;
        gap: 10px;
        padding: 10px;
        flex-shrink: 0;
    }}

    .scene-road {{
        position: absolute;
        background: rgba(123,132,145,0.55);
        z-index: 1;
        pointer-events: none;
    }}

    .scene-road::after {{
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        width: 600px;
        border-top: 2px dashed rgba(255,255,255,0.68);
    }}

    .scene-road-a {{
        left: -60px;
        top: 66px;
        width: 560px;
        height: 22px;
        transform: rotate(-6deg);
    }}

    .scene-road-b {{
        left: 190px;
        top: -40px;
        width: 22px;
        height: 220px;
        transform: rotate(10deg);
    }}

    .scene-section {{
        position: relative;
        z-index: 5;
        background: rgba(255,255,255,0.80);
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 8px;
    }}

    .scene-label {{
        font-size: 10.5px;
        font-weight: 900;
        color: #57606a;
        margin-bottom: 6px;
    }}

    .facility-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 6px;
    }}

    .facility-item {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        min-height: 48px;
        text-align: center;
        padding: 5px 3px;
        box-shadow: 0 3px 7px rgba(27,31,36,0.05);
    }}

    .facility-emoji {{
        width: 28px;
        height: 28px;
        margin: 0 auto 2px;
        border-radius: 10px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 17px;
    }}

    .facility-caption {{
        font-size: 8.5px;
        font-weight: 800;
        color: #374151;
        line-height: 1.1;
    }}

    .resident-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 6px;
    }}

    .resident-item {{
        position: relative;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        height: 39px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 7px rgba(27,31,36,0.05);
    }}

    .resident-person {{
        font-size: 20px;
    }}

    .resident-mood {{
        position: absolute;
        right: -4px;
        top: -5px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: #ffffff;
        border: 2px solid #d0d7de;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 9px;
        box-shadow: 0 3px 7px rgba(27,31,36,0.10);
    }}

    .comment-bubble {{
        min-height: 62px;
        background: rgba(255,255,255,0.97);
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 11px 13px;
        box-shadow: 0 6px 13px rgba(27,31,36,0.06);
        flex-shrink: 0;
    }}

    .comment-title {{
        font-size: 14px;
        font-weight: 900;
        color: #1f2328;
        margin-bottom: 5px;
    }}

    .comment-text {{
        font-size: 12px;
        color: #57606a;
        line-height: 1.4;
        white-space: normal;
    }}

    .district-score {{
        min-height: 66px;
        background: rgba(255,255,255,0.98);
        border: 1px solid #d0d7de;
        border-radius: 20px;
        display: grid;
        grid-template-columns: 46px 1fr 70px;
        gap: 10px;
        align-items: center;
        padding: 10px 12px;
        box-shadow: 0 6px 13px rgba(27,31,36,0.06);
        flex-shrink: 0;
        margin-top: auto;
    }}

    .score-face {{
        width: 42px;
        height: 42px;
        border-radius: 15px;
        background: #fff7ed;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 25px;
    }}

    .score-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 7px;
        margin-bottom: 6px;
    }}

    .score-state {{
        font-size: 14px;
        font-weight: 900;
        color: #1f2328;
    }}

    .score-stars {{
        font-size: 12.5px;
        color: #f59e0b;
        font-weight: 800;
    }}

    .score-bar {{
        height: 9px;
        background: #e5e7eb;
        border-radius: 999px;
        overflow: hidden;
    }}

    .score-fill {{
        height: 100%;
        border-radius: 999px;
    }}

    .score-num {{
        font-size: 31px;
        font-weight: 900;
        text-align: right;
        line-height: 1;
    }}

    .energy-section {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 26px;
        padding: 20px;
        box-shadow: 0 12px 24px rgba(27,31,36,0.06);
        margin-bottom: 22px;
    }}

    .energy-object-grid-section {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
    }}

    .energy-field-card {{
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-top: 4px solid var(--item-color);
        border-radius: 18px;
        padding: 13px;
        min-height: 210px;
    }}

    .energy-field-head {{
        display: grid;
        grid-template-columns: 42px 1fr;
        gap: 9px;
        align-items: center;
        margin-bottom: 11px;
    }}

    .energy-field-icon {{
        width: 40px;
        height: 40px;
        border-radius: 14px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 23px;
    }}

    .energy-field-name {{
        font-size: 14px;
        font-weight: 900;
        color: #1f2328;
    }}

    .energy-field-value {{
        font-size: 12px;
        color: var(--item-color);
        font-weight: 900;
    }}

    .energy-object-grid {{
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 7px;
        min-height: 88px;
        margin-bottom: 10px;
    }}

    .energy-object {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 13px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .energy-object-icon {{
        width: 31px;
        height: 31px;
        border-radius: 11px;
        background: var(--item-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 19px;
    }}

    .energy-empty {{
        grid-column: 1 / -1;
        color: #8c959f;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 82px;
        border: 1px dashed #d0d7de;
        border-radius: 13px;
        background: #ffffff;
    }}

    .energy-field-desc {{
        font-size: 11.5px;
        color: #57606a;
        line-height: 1.45;
    }}

    .reaction-box {{
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 22px;
        padding: 18px 20px;
        box-shadow: 0 8px 18px rgba(27,31,36,0.05);
        margin-bottom: 18px;
    }}

    .reaction-title {{
        font-size: 20px;
        font-weight: 900;
        color: #1f2328;
        margin-bottom: 8px;
    }}

    .reaction-desc {{
        font-size: 14px;
        color: #57606a;
        line-height: 1.7;
    }}

    .final-card {{
        background: linear-gradient(135deg, #f0fff4 0%, #ddf4ff 100%);
        border: 1px solid #aceebb;
        border-radius: 24px;
        padding: 22px 24px;
        box-shadow: 0 10px 22px rgba(27,31,36,0.05);
        margin-top: 10px;
    }}

    .final-title {{
        font-size: 24px;
        font-weight: 900;
        margin-bottom: 8px;
        color: #1f2328;
    }}

    .final-desc {{
        font-size: 14px;
        line-height: 1.7;
        color: #57606a;
        margin-bottom: 16px;
    }}

    .dash-link-btn {{
        display: inline-block;
        background: #0969da;
        color: white !important;
        text-decoration: none !important;
        padding: 11px 17px;
        border-radius: 13px;
        font-size: 13px;
        font-weight: 900;
        box-shadow: 0 7px 14px rgba(9,105,218,0.18);
    }}

    .dash-link-empty {{
        display: inline-block;
        background: rgba(255,255,255,0.78);
        border: 1px solid #d0d7de;
        border-radius: 13px;
        padding: 11px 13px;
        font-size: 12px;
        color: #57606a;
    }}

    .mini-note {{
        margin-top: 10px;
        font-size: 10.5px;
        color: #8c959f;
        line-height: 1.45;
    }}

    @media (max-width: 1100px) {{
        .hero-content,
        .hud-grid,
        .inventory-grid,
        .inventory-grid.energy,
        .energy-object-grid-section {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>

    <div class="root">
        <div class="hero">
            <div class="hero-content">
                <div>
                    <div class="hero-eyebrow">NOVA Village Simulation</div>
                    <div class="hero-title">A~E구역이 하나로 연결된 마을형 스마트시티 시뮬레이션</div>
                    <div class="hero-desc">
                        하나의 마을 지도 안에 A구역부터 E구역까지 함께 배치했습니다.
                        각 구역의 정책 아이템, 시설 변화, 주민 반응, 댓글, 만족도를 모두 보이도록 구조를 재정리했습니다.
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
                <div class="hud-value" style="font-size:23px;">{html_lib.escape(preset_choice)}</div>
                <div class="hud-sub">마을 전체에 정책 처치가 적용됩니다.</div>
            </div>

            <div class="hud-card">
                <div class="hud-label">시민 만족도 평균</div>
                <div class="hud-value">{avg:.1f}점</div>
                <div class="hud-sub">주민 표정과 댓글로 체감 만족도를 표현합니다.</div>
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
            내가 처치한 예산 배분을 게임 아이템처럼 표현했습니다.
        </div>
        <div class="inventory-grid">
            {budget_inventory}
        </div>

        <div class="section-title">⚡ 에너지 아이템 인벤토리</div>
        <div class="section-sub">
            에너지 배분도 아이템으로 표현했습니다.
        </div>
        <div class="inventory-grid energy">
            {energy_inventory}
        </div>

        <div class="section-title">🏘️ NOVA시 통합 마을 지도</div>
        <div class="section-sub">
            A~E구역이 하나의 마을 안에 함께 배치됩니다.
            각 구역에는 정책 아이템, 시설 오브젝트, 주민 이모지, 만족도 댓글이 표시됩니다.
        </div>

        <div class="village-scroll">
            <div class="village-board">
                <div class="village-title-card">
                    <div class="village-title">NOVA 통합 마을</div>
                    <div class="village-desc">
                        정책 처치에 따라 구역별 시설과 주민 반응이 달라집니다.
                    </div>
                </div>

                <div class="main-road road-1"></div>
                <div class="main-road road-2"></div>
                <div class="main-road road-3"></div>
                <div class="water-line"></div>

                {district_zones}
            </div>
        </div>

        <div class="energy-section">
            <div class="section-title">⚡ 에너지 아이템 필드</div>
            <div class="section-sub">
                에너지 오브젝트는 마을 지도와 겹치지 않도록 별도 필드로 분리했습니다.
            </div>
            <div class="energy-object-grid-section">
                {energy_field}
            </div>
        </div>

        <div class="reaction-box">
            <div class="reaction-title">🗣️ 마을 사람들의 전체 반응</div>
            <div class="reaction-desc">
                “마을 안에 어떤 정책 아이템이 들어왔는지, 그 결과로 어떤 시설이 생겼는지,
                그리고 주민들이 얼마나 만족하는지 댓글과 이모지로 확인할 수 있어요.”
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
                이 버전은 만족도 박스가 잘리지 않도록 구역 내부 높이와 전체 마을 비율을 다시 조정했습니다.
            </div>
        </div>
    </div>
    """

    return html


# ==================================================
# 사이드바
# ==================================================
with st.sidebar:
    st.markdown("## 🏘️ NOVA시 마을 시뮬레이터")
    st.caption("A~E구역이 하나의 마을로 구성되고, 정책 처치에 따라 주민 반응이 달라집니다.")

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
<div class="app-title">🏘️ NOVA시 마을형 스마트시티 시뮬레이션</div>
<div class="app-subtitle">
A구역부터 E구역까지 하나의 마을 안에 배치하고, 정책 처치에 따른 시설 변화와 주민 만족도를 댓글·이모지로 표현합니다.
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
- 마을형 지도 유지<br>
- 전체 구역 크기를 이전보다 축소해 화면 비율 개선<br>
- 만족도 박스가 잘리지 않도록 구역 내부 구조와 높이 재조정<br>
- 적용 아이템, 시설 변화, 주민 반응, 댓글, 만족도를 모두 분리해서 표시
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
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    solar,
    hydrogen,
    ess,
    external,
    result,
    dashboard_url
)

components.html(scene_html, height=3350, scrolling=True)

st.markdown("### 발표용 연결 멘트 예시")
st.markdown("""
이 1차 시뮬레이션은 A구역부터 E구역까지 하나의 마을로 구성된 스마트시티를 보여줍니다.  
예산과 에너지 배분이라는 정책 처치가 어떤 시설을 만들고, 그 결과 주민들이 어떤 표정과 댓글로 반응하는지를 확인한 뒤,  
2차 대시보드에서 같은 입력값을 정량적으로 분석하겠습니다.
""")
