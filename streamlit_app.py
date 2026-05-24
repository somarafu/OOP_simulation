"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOVA시 스마트시티 게임형 정책 처치 시뮬레이션
simulation_story.py

역할:
- 1차 결과물: 예산·에너지 배분 처치가 도시 구조를 바꾸는 장면을 게임처럼 시각화
- 2차 결과물: 기존 dashboard.py에서 만족도·자립률·구역별 결과를 상세 분석

실행:
streamlit run simulation_story.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import html as html_lib
import urllib.parse
from itertools import cycle

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(__file__))

# ==================================================
# classes.py가 있으면 실제 OOP 모델을 사용하고,
# 없거나 오류가 나면 화면용 간이 계산으로 대체
# ==================================================
try:
    from classes import (
        Worker, Student, Caregiver, Unemployed, Elder,
        SolarPanel, HydrogenCell, ESS, ExternalGrid,
        Resource, EnergyGrid, District, City,
        BudgetAllocationError, EnergyAllocationError
    )
    HAS_CLASSES = True
except Exception:
    HAS_CLASSES = False


# ==================================================
# 페이지 설정
# ==================================================
st.set_page_config(
    page_title="NOVA시 게임형 정책 처치 시뮬레이션",
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
        "short": "A구역",
        "name": "산업단지",
        "emoji": "🏭",
        "desc": "근로자 중심 · 이동성·일자리 민감",
        "weights": {
            "welfare": 0.35,
            "education": 0.25,
            "energy_infra": 1.10,
            "general_infra": 1.25,
            "safety": 0.80,
        },
    },
    "B구역(대학가)": {
        "short": "B구역",
        "name": "대학가",
        "emoji": "🎓",
        "desc": "학생 중심 · 교육·문화 민감",
        "weights": {
            "welfare": 0.30,
            "education": 1.45,
            "energy_infra": 0.45,
            "general_infra": 0.80,
            "safety": 0.55,
        },
    },
    "C구역(복지타운)": {
        "short": "C구역",
        "name": "복지타운",
        "emoji": "🏥",
        "desc": "노인·취약계층 중심 · 복지·안전 민감",
        "weights": {
            "welfare": 1.50,
            "education": 0.30,
            "energy_infra": 0.45,
            "general_infra": 0.55,
            "safety": 0.95,
        },
    },
    "D구역(신도시)": {
        "short": "D구역",
        "name": "신도시",
        "emoji": "🏙️",
        "desc": "혼합형 시민 구성 · 균형 정책 반응",
        "weights": {
            "welfare": 0.80,
            "education": 0.85,
            "energy_infra": 0.95,
            "general_infra": 1.00,
            "safety": 0.85,
        },
    },
    "E구역(구도심)": {
        "short": "E구역",
        "name": "구도심",
        "emoji": "🏚️",
        "desc": "노후 인프라 · 복지·안전·생활SOC 민감",
        "weights": {
            "welfare": 1.05,
            "education": 0.45,
            "energy_infra": 0.45,
            "general_infra": 0.95,
            "safety": 1.10,
        },
    },
}


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


def expected_energy_self_rate(solar, hydrogen, ess, external):
    return (solar * 0.7 + hydrogen * 0.9 + ess * 0.6 + external * 0.0) / 100


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
    classes.py가 있으면 실제 OOP 모델을 사용한다.
    오류가 나거나 classes.py가 없으면 게임 화면용 간이 점수를 사용한다.
    """
    if HAS_CLASSES:
        try:
            resource = Resource(
                welfare=welfare / 100,
                education=education / 100,
                energy_infra=energy_infra / 100,
                general_infra=general_infra / 100,
                safety=safety / 100,
            )

            grid = EnergyGrid([
                SolarPanel(solar / 100),
                HydrogenCell(hydrogen / 100),
                ESS(ess / 100),
                ExternalGrid(external / 100),
            ])

            city = get_city()
            result = city.apply_policy(resource, grid)

            scores = {
                key: float(result["districts"][key])
                for key in DISTRICT_KEYS
            }

            avg = float(result["city_average"])
            independence = float(result["independence_rate"])
            warnings = result.get("warnings", [])

            return {
                "scores": scores,
                "average": avg,
                "independence": independence,
                "warnings": warnings,
                "source": "classes.py OOP 모델",
            }

        except Exception:
            pass

    # fallback: 화면용 간이 계산
    energy_rate = expected_energy_self_rate(solar, hydrogen, ess, external)
    energy_bonus = (energy_rate - 0.4) * 18

    scores = {
        "A구역(산업단지)": 42 + general_infra * 0.30 + energy_infra * 0.18 + safety * 0.15 + education * 0.08 + welfare * 0.05 + energy_bonus,
        "B구역(대학가)": 40 + education * 0.33 + general_infra * 0.14 + safety * 0.08 + energy_infra * 0.08 + welfare * 0.05 + energy_bonus,
        "C구역(복지타운)": 38 + welfare * 0.38 + safety * 0.18 + general_infra * 0.08 + education * 0.05 + energy_infra * 0.05 + energy_bonus,
        "D구역(신도시)": 43 + welfare * 0.16 + education * 0.16 + energy_infra * 0.16 + general_infra * 0.18 + safety * 0.14 + energy_bonus,
        "E구역(구도심)": 36 + welfare * 0.22 + safety * 0.22 + general_infra * 0.20 + education * 0.06 + energy_infra * 0.07 + energy_bonus,
    }

    scores = {
        key: max(30, min(95, value))
        for key, value in scores.items()
    }

    avg = sum(scores.values()) / len(scores)
    warnings = [key for key, value in scores.items() if value < 50]

    return {
        "scores": scores,
        "average": avg,
        "independence": energy_rate,
        "warnings": warnings,
        "source": "화면용 간이 계산",
    }


# ==================================================
# HTML 생성 유틸
# ==================================================
def score_face(score):
    if score < 50:
        return "😟"
    if score < 60:
        return "😐"
    if score < 75:
        return "🙂"
    return "😄"


def score_color(score):
    if score < 50:
        return "#cf222e"
    if score < 60:
        return "#9a6700"
    if score < 75:
        return "#0969da"
    return "#1a7f37"


def clamp(n, low, high):
    return max(low, min(high, n))


def icon_count(value, weight=1.0, max_icons=7):
    count = round((value * weight) / 12)
    return clamp(count, 0, max_icons)


def make_icon_spans(symbols, count, base_delay=1.0):
    if count <= 0:
        return ""

    result = []
    symbol_cycle = cycle(symbols)

    for i in range(count):
        symbol = next(symbol_cycle)
        delay = base_delay + i * 0.13
        result.append(
            f'<span class="facility" style="animation-delay:{delay:.2f}s">{symbol}</span>'
        )

    return "".join(result)


def make_people(score, district_index):
    face = score_face(score)
    people = []

    for i in range(5):
        delay = 7.8 + district_index * 0.25 + i * 0.15
        top = 64 + (i % 2) * 18
        left = 8 + i * 17

        people.append(
            f"""
            <span class="citizen"
                  style="left:{left}%; top:{top}%; animation-delay:{delay:.2f}s">
                {face}
            </span>
            """
        )

    return "".join(people)


def district_facilities(
    district_key,
    welfare,
    education,
    energy_infra,
    general_infra,
    safety,
    district_index,
):
    weights = DISTRICT_INFO[district_key]["weights"]

    welfare_icons = make_icon_spans(
        ["🏥", "👩‍⚕️", "🏘️"],
        icon_count(welfare, weights["welfare"], 7),
        1.8 + district_index * 0.1,
    )

    education_icons = make_icon_spans(
        ["🏫", "📚", "🎓"],
        icon_count(education, weights["education"], 7),
        2.5 + district_index * 0.1,
    )

    energy_icons = make_icon_spans(
        ["🔌", "📡", "🚗"],
        icon_count(energy_infra, weights["energy_infra"], 7),
        3.2 + district_index * 0.1,
    )

    infra_icons = make_icon_spans(
        ["🚌", "🛣️", "🌳"],
        icon_count(general_infra, weights["general_infra"], 7),
        3.9 + district_index * 0.1,
    )

    safety_icons = make_icon_spans(
        ["👮", "🚓", "📹", "🚒"],
        icon_count(safety, weights["safety"], 7),
        4.6 + district_index * 0.1,
    )

    return welfare_icons + education_icons + energy_icons + infra_icons + safety_icons


def energy_facilities(solar, hydrogen, ess, external):
    solar_html = make_icon_spans(["☀️", "🔆", "🏠"], icon_count(solar, 1.2, 9), 5.0)
    hydrogen_html = make_icon_spans(["💧", "⚗️", "🏭"], icon_count(hydrogen, 1.2, 9), 5.4)
    ess_html = make_icon_spans(["🔋", "⚡"], icon_count(ess, 1.2, 9), 5.8)
    external_html = make_icon_spans(["🗼", "🔌"], icon_count(external, 1.0, 9), 6.2)

    return solar_html, hydrogen_html, ess_html, external_html


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
        2차 상세 대시보드 열기 →
    </a>
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
    warnings = model_result["warnings"]
    model_source = model_result["source"]

    solar_html, hydrogen_html, ess_html, external_html = energy_facilities(
        solar, hydrogen, ess, external
    )

    district_cards = []

    for idx, district_key in enumerate(DISTRICT_KEYS):
        info = DISTRICT_INFO[district_key]
        score = scores[district_key]
        color = score_color(score)
        face = score_face(score)

        facilities = district_facilities(
            district_key,
            welfare,
            education,
            energy_infra,
            general_infra,
            safety,
            idx,
        )

        people = make_people(score, idx)

        district_cards.append(
            f"""
            <div class="district district-{idx + 1}">
                <div class="district-top">
                    <div class="district-emoji">{info["emoji"]}</div>
                    <div>
                        <div class="district-title">{info["short"]} · {info["name"]}</div>
                        <div class="district-desc">{info["desc"]}</div>
                    </div>
                </div>

                <div class="building-zone">
                    {facilities}
                    {people}
                    <div class="road-line"></div>
                </div>

                <div class="score-panel">
                    <div class="score-face">{face}</div>
                    <div class="score-content">
                        <div class="score-label">시민 만족도 변화</div>
                        <div class="score-bar">
                            <div class="score-fill"
                                 style="--score-width:{score:.1f}%; --score-color:{color};">
                            </div>
                        </div>
                    </div>
                    <div class="score-value" style="color:{color};">{score:.1f}</div>
                </div>
            </div>
            """
        )

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

    if dashboard_button:
        dashboard_html = dashboard_button
    else:
        dashboard_html = """
        <div class="dashboard-empty">
            2차 대시보드 URL을 왼쪽 사이드바에 입력하면 여기에서 바로 이동할 수 있습니다.
        </div>
        """

    warning_text = (
        f"{len(warnings)}개 구역 주의 필요"
        if warnings
        else "위험 구역 없음"
    )

    css = """
    <style>
    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        background: #ffffff;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #1f2328;
    }

    .game-root {
        padding: 10px 8px 26px;
    }

    .game-hero {
        position: relative;
        overflow: hidden;
        border-radius: 28px;
        padding: 34px 38px;
        color: white;
        background:
            radial-gradient(circle at 8% 20%, rgba(255,255,255,0.20), transparent 24%),
            radial-gradient(circle at 88% 18%, rgba(255,255,255,0.16), transparent 26%),
            linear-gradient(135deg, #0969da 0%, #8250df 100%);
        box-shadow: 0 18px 42px rgba(9,105,218,0.22);
        margin-bottom: 24px;
    }

    .game-hero::after {
        content: "☁️";
        position: absolute;
        font-size: 72px;
        right: 40px;
        top: 18px;
        opacity: 0.22;
        animation: cloudFloat 5s ease-in-out infinite alternate;
    }

    @keyframes cloudFloat {
        from { transform: translateX(0); }
        to { transform: translateX(-28px); }
    }

    .eyebrow {
        font-size: 13px;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        font-weight: 900;
        opacity: 0.9;
        margin-bottom: 10px;
    }

    .hero-title {
        font-size: 38px;
        font-weight: 950;
        line-height: 1.2;
        margin-bottom: 12px;
    }

    .hero-desc {
        font-size: 16px;
        line-height: 1.75;
        opacity: 0.96;
        max-width: 980px;
    }

    .hud {
        display: grid;
        grid-template-columns: 1.2fr 1fr 1fr 1fr;
        gap: 14px;
        margin-bottom: 20px;
    }

    .hud-card {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 20px;
        padding: 18px 20px;
        box-shadow: 0 10px 26px rgba(27,31,36,0.07);
        min-height: 112px;
        animation: fadeUp 0.8s ease both;
    }

    .hud-label {
        font-size: 12px;
        color: #656d76;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .hud-value {
        font-size: 28px;
        font-weight: 950;
        color: #0969da;
        line-height: 1.1;
    }

    .hud-sub {
        margin-top: 8px;
        font-size: 13px;
        color: #57606a;
        line-height: 1.5;
    }

    .timeline {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 22px;
    }

    .timeline-step {
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 18px;
        padding: 14px 12px;
        text-align: center;
        min-height: 120px;
        animation: stepPulse 8s ease both;
    }

    .timeline-step:nth-child(1) { animation-delay: 0.2s; }
    .timeline-step:nth-child(2) { animation-delay: 1.6s; }
    .timeline-step:nth-child(3) { animation-delay: 3.0s; }
    .timeline-step:nth-child(4) { animation-delay: 4.4s; }
    .timeline-step:nth-child(5) { animation-delay: 5.8s; }

    @keyframes stepPulse {
        0%, 12% {
            transform: translateY(0);
            background: linear-gradient(135deg, #ddf4ff, #ffffff);
            border-color: #0969da;
            box-shadow: 0 10px 26px rgba(9,105,218,0.16);
        }
        22%, 100% {
            transform: translateY(0);
            background: #f6f8fa;
            border-color: #d0d7de;
            box-shadow: none;
        }
    }

    .timeline-icon {
        font-size: 28px;
        margin-bottom: 7px;
    }

    .timeline-title {
        font-size: 14px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 5px;
    }

    .timeline-desc {
        font-size: 12px;
        color: #57606a;
        line-height: 1.45;
    }

    .city-stage {
        position: relative;
        overflow: hidden;
        border: 1px solid #d0d7de;
        border-radius: 30px;
        background:
            linear-gradient(180deg, #ddf4ff 0%, #f6fbff 38%, #f0fff4 100%);
        padding: 22px;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.7),
                    0 14px 34px rgba(27,31,36,0.08);
        margin-bottom: 24px;
    }

    .city-stage::before {
        content: "☀️";
        position: absolute;
        top: 22px;
        right: 34px;
        font-size: 50px;
        animation: sunSpin 10s linear infinite;
    }

    @keyframes sunSpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .stage-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
        margin-bottom: 18px;
        padding-right: 80px;
    }

    .stage-title {
        font-size: 26px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 6px;
    }

    .stage-desc {
        font-size: 14px;
        color: #57606a;
        line-height: 1.65;
    }

    .city-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
    }

    .district {
        position: relative;
        background: rgba(255,255,255,0.92);
        border: 1px solid #d0d7de;
        border-radius: 24px;
        padding: 16px 14px;
        min-height: 390px;
        box-shadow: 0 10px 24px rgba(27,31,36,0.07);
        overflow: hidden;
        animation: fadeUp 0.7s ease both;
    }

    .district-1 { animation-delay: 0.4s; }
    .district-2 { animation-delay: 0.6s; }
    .district-3 { animation-delay: 0.8s; }
    .district-4 { animation-delay: 1.0s; }
    .district-5 { animation-delay: 1.2s; }

    @keyframes fadeUp {
        from { transform: translateY(18px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    .district-top {
        display: flex;
        gap: 10px;
        align-items: center;
        margin-bottom: 12px;
    }

    .district-emoji {
        width: 46px;
        height: 46px;
        border-radius: 16px;
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 25px;
        flex: 0 0 auto;
    }

    .district-title {
        font-size: 15px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 3px;
    }

    .district-desc {
        font-size: 11px;
        color: #57606a;
        line-height: 1.35;
    }

    .building-zone {
        position: relative;
        background:
            linear-gradient(180deg, rgba(221,244,255,0.55) 0%, rgba(246,248,250,0.9) 70%),
            repeating-linear-gradient(90deg, transparent 0 22px, rgba(208,215,222,0.35) 22px 23px);
        border: 1px dashed #d0d7de;
        border-radius: 18px;
        padding: 12px;
        min-height: 210px;
        display: flex;
        flex-wrap: wrap;
        align-content: flex-start;
        justify-content: center;
        gap: 8px;
        overflow: hidden;
        margin-bottom: 14px;
    }

    .building-zone::after {
        content: "";
        position: absolute;
        bottom: 20px;
        left: 0;
        width: 100%;
        height: 28px;
        background: #8c959f;
        opacity: 0.22;
    }

    .road-line {
        position: absolute;
        bottom: 32px;
        left: 0;
        width: 200%;
        height: 2px;
        border-top: 2px dashed #ffffff;
        opacity: 0.9;
        animation: roadMove 2.8s linear infinite;
    }

    @keyframes roadMove {
        from { transform: translateX(0); }
        to { transform: translateX(-80px); }
    }

    .facility {
        position: relative;
        z-index: 2;
        display: inline-block;
        font-size: 27px;
        opacity: 0;
        transform: scale(0.3) translateY(18px);
        animation: facilityPop 0.55s cubic-bezier(.2,.8,.2,1.25) forwards;
    }

    @keyframes facilityPop {
        to {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }

    .citizen {
        position: absolute;
        z-index: 4;
        font-size: 22px;
        opacity: 0;
        animation: citizenEnter 0.65s ease forwards,
                   citizenWalk 3.2s ease-in-out infinite alternate;
    }

    @keyframes citizenEnter {
        from { opacity: 0; transform: translateY(12px) scale(0.6); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes citizenWalk {
        from { margin-left: -5px; }
        to { margin-left: 9px; }
    }

    .score-panel {
        display: grid;
        grid-template-columns: 34px 1fr 46px;
        gap: 10px;
        align-items: center;
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 16px;
        padding: 12px;
    }

    .score-face {
        font-size: 25px;
    }

    .score-label {
        font-size: 11px;
        font-weight: 900;
        color: #57606a;
        margin-bottom: 6px;
    }

    .score-bar {
        height: 10px;
        background: #d0d7de;
        border-radius: 999px;
        overflow: hidden;
    }

    .score-fill {
        height: 100%;
        width: 0;
        background: var(--score-color);
        border-radius: 999px;
        animation: scoreFill 1.2s ease forwards;
        animation-delay: 8.3s;
    }

    @keyframes scoreFill {
        to { width: var(--score-width); }
    }

    .score-value {
        font-size: 16px;
        font-weight: 950;
        text-align: right;
    }

    .energy-stage {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 28px;
        padding: 24px;
        box-shadow: 0 12px 30px rgba(27,31,36,0.07);
        margin-bottom: 24px;
    }

    .energy-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
    }

    .energy-card {
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 22px;
        padding: 16px;
        min-height: 210px;
        text-align: center;
        overflow: hidden;
    }

    .energy-title {
        font-size: 15px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 6px;
    }

    .energy-desc {
        font-size: 12px;
        color: #57606a;
        line-height: 1.45;
        margin-bottom: 12px;
    }

    .energy-icons {
        background: #ffffff;
        border: 1px dashed #d0d7de;
        border-radius: 16px;
        padding: 12px;
        min-height: 112px;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-content: flex-start;
        gap: 8px;
    }

    .bridge {
        display: grid;
        grid-template-columns: 1fr 60px 1fr;
        gap: 14px;
        align-items: center;
        margin-bottom: 24px;
    }

    .bridge-card {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 24px;
        padding: 22px;
        box-shadow: 0 10px 26px rgba(27,31,36,0.07);
        min-height: 150px;
    }

    .bridge-title {
        font-size: 21px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 8px;
    }

    .bridge-desc {
        font-size: 14px;
        color: #57606a;
        line-height: 1.7;
    }

    .bridge-arrow {
        text-align: center;
        font-size: 42px;
        color: #0969da;
        font-weight: 950;
        animation: arrowNudge 1s ease-in-out infinite alternate;
    }

    @keyframes arrowNudge {
        from { transform: translateX(0); }
        to { transform: translateX(8px); }
    }

    .final-panel {
        background: linear-gradient(135deg, #f0fff4 0%, #ddf4ff 100%);
        border: 1px solid #aceebb;
        border-radius: 28px;
        padding: 26px 28px;
        box-shadow: 0 12px 28px rgba(27,31,36,0.06);
    }

    .final-title {
        font-size: 27px;
        font-weight: 950;
        color: #1f2328;
        margin-bottom: 10px;
    }

    .final-desc {
        font-size: 15px;
        color: #57606a;
        line-height: 1.75;
        margin-bottom: 16px;
    }

    .dashboard-button {
        display: inline-block;
        background: #0969da;
        color: white !important;
        text-decoration: none !important;
        padding: 13px 18px;
        border-radius: 15px;
        font-size: 14px;
        font-weight: 950;
        box-shadow: 0 8px 18px rgba(9,105,218,0.22);
    }

    .dashboard-empty {
        background: rgba(255,255,255,0.74);
        border: 1px solid #d0d7de;
        border-radius: 16px;
        padding: 14px 16px;
        font-size: 13px;
        color: #57606a;
        display: inline-block;
    }

    @media (max-width: 1100px) {
        .hud,
        .timeline,
        .city-grid,
        .energy-grid,
        .bridge {
            grid-template-columns: 1fr;
        }

        .bridge-arrow {
            transform: rotate(90deg);
        }
    }
    </style>
    """

    body = f"""
    <div class="game-root">
        <section class="game-hero">
            <div class="eyebrow">NOVA Smart City Game Simulation</div>
            <div class="hero-title">예산과 에너지 처치가<br>도시를 바꾸는 장면</div>
            <div class="hero-desc">
                왼쪽에서 설정한 비율에 따라 A구역부터 E구역까지 도시 시설이 다르게 생겨납니다.
                복지 예산은 병원과 돌봄 시설로, 교육 예산은 학교와 도서관으로,
                안전 예산은 경찰과 CCTV로, 에너지 예산은 충전소와 스마트그리드로 표현됩니다.
            </div>
        </section>

        <section class="hud">
            <div class="hud-card">
                <div class="hud-label">현재 프리셋</div>
                <div class="hud-value" style="font-size:24px;">{html_lib.escape(preset_choice)}</div>
                <div class="hud-sub">선택한 정책 조합이 도시 장면에 적용됩니다.</div>
            </div>
            <div class="hud-card">
                <div class="hud-label">도시 평균 만족도</div>
                <div class="hud-value">{avg:.1f}점</div>
                <div class="hud-sub">자세한 원인은 2차 대시보드에서 분석합니다.</div>
            </div>
            <div class="hud-card">
                <div class="hud-label">에너지 자립률</div>
                <div class="hud-value">{independence * 100:.1f}%</div>
                <div class="hud-sub">태양광·수소·ESS 설비의 종합 효과입니다.</div>
            </div>
            <div class="hud-card">
                <div class="hud-label">주의 상태</div>
                <div class="hud-value" style="color:{'#cf222e' if warnings else '#1a7f37'};">{warning_text}</div>
                <div class="hud-sub">계산 기준: {html_lib.escape(model_source)}</div>
            </div>
        </section>

        <section class="timeline">
            <div class="timeline-step">
                <div class="timeline-icon">🎛️</div>
                <div class="timeline-title">1. 정책 투입</div>
                <div class="timeline-desc">예산·에너지 배분 선택</div>
            </div>
            <div class="timeline-step">
                <div class="timeline-icon">🏗️</div>
                <div class="timeline-title">2. 시설 생성</div>
                <div class="timeline-desc">학교·병원·경찰·도로 증가</div>
            </div>
            <div class="timeline-step">
                <div class="timeline-icon">⚡</div>
                <div class="timeline-title">3. 에너지 설비</div>
                <div class="timeline-desc">태양광·수소·ESS 배치</div>
            </div>
            <div class="timeline-step">
                <div class="timeline-icon">😊</div>
                <div class="timeline-title">4. 시민 반응</div>
                <div class="timeline-desc">구역별 만족도 변화</div>
            </div>
            <div class="timeline-step">
                <div class="timeline-icon">📊</div>
                <div class="timeline-title">5. 상세 분석</div>
                <div class="timeline-desc">2차 대시보드에서 확인</div>
            </div>
        </section>

        <section class="bridge">
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
                    배분값이 클수록 해당 시설 아이콘이 더 많이 생성됩니다.
                    이 화면은 “왜 점수가 그렇게 나왔는가”를 설명하기 전,
                    처치가 도시 장면으로 바뀌는 과정을 보여줍니다.
                </div>
            </div>
        </section>

        <section class="city-stage">
            <div class="stage-header">
                <div>
                    <div class="stage-title">A~E구역 도시 변화 맵</div>
                    <div class="stage-desc">
                        각 구역의 성격에 따라 같은 예산도 다르게 표현됩니다.
                        예를 들어 대학가는 교육 예산에 민감하고, 복지타운은 복지·안전 예산에 민감합니다.
                    </div>
                </div>
            </div>

            <div class="city-grid">
                {''.join(district_cards)}
            </div>
        </section>

        <section class="energy-stage">
            <div class="stage-title">에너지 설비 변화</div>
            <div class="stage-desc">
                에너지 배분은 도시 외곽의 발전·저장 설비로 표현됩니다.
                태양광, 수소연료전지, ESS가 늘어날수록 외부 전력망 의존을 낮추는 방향으로 작동합니다.
            </div>

            <div class="energy-grid">
                <div class="energy-card">
                    <div class="energy-title">태양광 구역</div>
                    <div class="energy-desc">지붕형 태양광과 태양광 패널이 늘어납니다.</div>
                    <div class="energy-icons">{solar_html}</div>
                </div>
                <div class="energy-card">
                    <div class="energy-title">수소연료전지 구역</div>
                    <div class="energy-desc">안정적인 도시 전력 생산 설비가 늘어납니다.</div>
                    <div class="energy-icons">{hydrogen_html}</div>
                </div>
                <div class="energy-card">
                    <div class="energy-title">ESS 저장 구역</div>
                    <div class="energy-desc">남는 전기를 저장하는 배터리 시설이 늘어납니다.</div>
                    <div class="energy-icons">{ess_html}</div>
                </div>
                <div class="energy-card">
                    <div class="energy-title">외부전력망 의존</div>
                    <div class="energy-desc">도시 바깥의 전력망에 의존하는 구조입니다.</div>
                    <div class="energy-icons">{external_html}</div>
                </div>
            </div>
        </section>

        <section class="final-panel">
            <div class="final-title">🎮 1차 게임형 시뮬레이션 완료</div>
            <div class="final-desc">
                이 화면은 정책 처치가 도시 안에서 어떤 시설과 장면으로 나타나는지를 보여주는 1차 시뮬레이션입니다.
                이제 같은 입력값을 바탕으로 2차 대시보드에서 구역별 만족도, 에너지 자립률,
                시나리오 비교와 시스템 분석을 확인하면 됩니다.
            </div>
            {dashboard_html}
        </section>
    </div>
    """

    return css + body


# ==================================================
# 사이드바
# ==================================================
with st.sidebar:
    st.markdown("## 🎮 게임형 정책 처치 설정")
    st.caption("이 화면은 결과 분석보다, 정책이 도시 장면을 어떻게 바꾸는지 보여주는 1차 시뮬레이션입니다.")

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
    default_dashboard_url = get_dashboard_url_from_secrets()
    dashboard_url = st.text_input(
        "2차 대시보드 URL",
        value=default_dashboard_url,
        placeholder="예: https://your-dashboard.streamlit.app",
    )
    st.caption("기존 dashboard.py를 별도 앱으로 배포했다면 그 URL을 입력하세요.")

    play = st.button("▶ 도시 변화 시뮬레이션 재생", type="primary", use_container_width=True)


# ==================================================
# 메인 화면
# ==================================================
st.markdown(
    """
    <style>
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
    </style>
    <div class="main-title">🎮 NOVA시 게임형 정책 처치 시뮬레이션</div>
    <div class="main-subtitle">
        이 화면은 2차 대시보드의 상세 결과를 보여주기 전,
        예산·에너지 배분이라는 정책 처치가 A~E구역의 도시 구조를 어떻게 바꾸는지
        게임 화면처럼 보여주는 1차 시뮬레이션입니다.
    </div>
    """,
    unsafe_allow_html=True,
)

if not budget_ok or not energy_ok:
    st.markdown(
        """
        <div class="guide-box">
            <b>시뮬레이션 실행 조건</b><br>
            예산 배분 합계와 에너지 배분 합계가 각각 정확히 100%가 되어야 합니다.
            왼쪽 사이드바에서 비율을 조정한 뒤 다시 실행해 주세요.
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

if not play:
    st.markdown(
        """
        <div class="guide-box">
            왼쪽에서 정책 처치를 설정한 뒤 <b>도시 변화 시뮬레이션 재생</b> 버튼을 누르세요.
            버튼을 누르면 시설이 순서대로 나타나고, 시민 만족도 막대가 채워지면서
            도시가 변화하는 장면이 재생됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

components.html(
    make_game_html(
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
    ),
    height=1450,
    scrolling=True,
)

st.markdown("### 발표 연결 문장 예시")
st.markdown(
    """
    이 1차 시뮬레이션은 정책 처치가 도시 장면에 어떻게 반영되는지를 보여줍니다.  
    이제 같은 입력값을 2차 대시보드에서 확인하면서, 실제 시민 만족도와 에너지 자립률이 어떻게 달라졌는지 분석하겠습니다.
    """
)
