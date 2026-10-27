
import os
from functools import wraps
from collections import defaultdict
from statistics import mean, median

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

from db import get_db_connection


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY environment variable is not set.")
CSRFProtect(app)
@app.route("/health")
def health():
    return {"status": "ok"}, 200


# ==================================================
# COMMON HELPERS
# ==================================================

def admin_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in as an administrator first.", "error")
            return redirect(url_for("admin_login"))
        return view_function(*args, **kwargs)
    return wrapped_view


def write_audit_log(cursor, action, details):
    cursor.execute(
        """
        INSERT INTO audit_logs (admin_id, action, details)
        VALUES (%s, %s, %s)
        """,
        (session.get("admin_id"), action, details[:500])
    )



def read_valid_year(raw_year):
    if not raw_year:
        return ""

    try:
        year = int(raw_year)
        if 1900 <= year <= 2100:
            return str(year)
    except (TypeError, ValueError):
        pass

    return ""


def clean_text(value):
    return str(value or "").strip()


def as_number(value):
    try:
        number = float(value)
        if -1e15 < number < 1e15:
            return number
    except (TypeError, ValueError):
        pass
    return None


def is_non_detect(qualifier):
    qualifier = clean_text(qualifier).lower()
    return (
        "not detected" in qualifier
        or "non-detect" in qualifier
        or "nondetect" in qualifier
    )


def get_comparable_values(records):
    """
    Separate values by unit and sample matrix.
    Values from different units or matrices must not be
    directly compared.
    """
    groups = defaultdict(list)

    for row in records:
        value = as_number(row.get("value"))

        if value is None or is_non_detect(row.get("qualifier")):
            continue

        unit = clean_text(row.get("unit"))
        matrix = clean_text(row.get("matrix")).lower()

        if not unit:
            continue

        groups[(unit, matrix)].append(value)

    return groups

    def classify_pollutant_risk(pollutant, sample_matrix, concentration):

    """

    Classifies risk based on pollutant and sample matrix (Water, Tissue, Sediment).

    """

    pollutant_lower = clean_text(pollutant).lower()

    matrix_lower = clean_text(sample_matrix).lower()



    if "mercury" in pollutant_lower:

        if "water" in matrix_lower:

            if concentration < 0.001: return 'Low'

            elif concentration <= 0.005: return 'Moderate'

            else: return 'High'

        elif "tissue" in matrix_lower or "mussel" in matrix_lower:

            if concentration < 0.1: return 'Low'

            elif concentration <= 0.3: return 'Moderate'

            else: return 'High'

            

    if concentration < 10:

        return 'Low'

    elif concentration <= 50:

        return 'Moderate'

    else:

        return 'High'

def clean_text(text):
    return str(text).strip() if text else ""


# ==================================================
# POLLUTANT-SPECIFIC EDUCATIONAL GUIDANCE
# ==================================================

def pollutant_guidance(parameter):
    """
    General scientific context for a pollutant label.

    These are possible sources to investigate, not causes
    confirmed by the dataset.
    """
    label = clean_text(parameter).lower()

    if not label:
        return {
            "category": "Multiple pollutant types",
            "causes": [
                "No single source explanation is appropriate when "
                "multiple pollutant types are selected."
            ],
            "precautions": [
                "Select a pollutant to see more relevant guidance.",
                "Check units, sample matrix, qualifier, and detection limit.",
                "Use local evidence and repeat sampling before drawing conclusions."
            ]
        }

    if any(term in label for term in [
        "pcb", "polychlorinated biphenyl"
    ]):
        return {
            "category": "Persistent industrial chemical",
            "causes": [
                "Historical electrical equipment, industrial materials, "
                "legacy waste, and contaminated sediment are possible "
                "sources worth investigating for PCBs.",
                "PCBs can persist in the environment and may accumulate "
                "in some food webs, depending on the compound and conditions."
            ],
            "precautions": [
                "Review historical industrial and waste-disposal records "
                "near the sampling area.",
                "Use validated laboratory methods and comparable samples "
                "to confirm results.",
                "Follow official seafood advisories where applicable; "
                "do not infer food safety from one measurement."
            ]
        }

    if any(term in label for term in [
        "mercury", "methylmercury"
    ]):
        return {
            "category": "Potentially toxic metal",
            "causes": [
                "Possible pathways include industrial emissions or discharge, "
                "historical mining, contaminated sediment, and atmospheric "
                "deposition. The relevant pathway depends on the location.",
                "Some forms of mercury can be transformed into methylmercury "
                "and accumulate in aquatic food webs."
            ],
            "precautions": [
                "Confirm the mercury species, sample matrix, unit, and "
                "laboratory method before interpreting the value.",
                "Investigate plausible upstream industrial, sediment, "
                "and atmospheric pathways using local evidence.",
                "Use official seafood guidance rather than making a "
                "health-risk judgement from a single record."
            ]
        }

    if "lead" in label:
        return {
            "category": "Potentially toxic metal",
            "causes": [
                "Possible pathways include industrial discharge, urban "
                "runoff, historical paint or infrastructure, and contaminated "
                "sediment.",
                "Local drainage patterns and historical land use can help "
                "identify which sources warrant investigation."
            ],
            "precautions": [
                "Check nearby stormwater outlets, industrial sites, and "
                "historical land use.",
                "Repeat sampling using the same matrix, unit, and method.",
                "Use environmental guidance and confirmatory testing "
                "before recommending cleanup."
            ]
        }

    if "cadmium" in label:
        return {
            "category": "Potentially toxic metal",
            "causes": [
                "Possible pathways include industrial discharge, metal "
                "processing, battery-related waste, and contaminated "
                "sediment.",
                "These sources are hypotheses; local facility and discharge "
                "records would be needed to investigate them."
            ],
            "precautions": [
                "Review local industrial and waste-disposal pathways.",
                "Confirm the result with an appropriate laboratory method.",
                "Compare only measurements with compatible units and "
                "sample matrices."
            ]
        }

    if "arsenic" in label:
        return {
            "category": "Metalloid",
            "causes": [
                "Arsenic may come from natural geology as well as mining, "
                "industrial activities, or contaminated sediment.",
                "The measurement alone cannot distinguish a natural source "
                "from a human-caused source."
            ],
            "precautions": [
                "Consider local geology alongside industrial and land-use "
                "records.",
                "Confirm the arsenic concentration and, where relevant, "
                "its chemical form.",
                "Do not attribute the result to an industrial source "
                "without supporting evidence."
            ]
        }

    if any(term in label for term in [
        "chromium", "nickel", "copper", "zinc"
    ]):
        metal_name = next(
            term for term in [
                "chromium", "nickel", "copper", "zinc"
            ] if term in label
        )

        return {
            "category": "Metal",
            "causes": [
                f"Possible pathways for {metal_name} include industrial "
                "discharge, urban runoff, port or vessel activity, and "
                "contaminated sediment.",
                "The relative importance of these pathways depends on "
                "local land use, drainage, geology, and the form of the metal."
            ],
            "precautions": [
                "Review local stormwater, industrial, and port-related "
                "discharge information where relevant.",
                "Check whether the result is for dissolved or total metal "
                "and confirm the unit and sample matrix.",
                "Repeat comparable sampling before assessing a change "
                "over time."
            ]
        }

    if any(term in label for term in [
        "oil", "petroleum", "hydrocarbon", "pah",
        "polycyclic aromatic"
    ]):
        return {
            "category": "Oil-related or organic contaminant",
            "causes": [
                "Possible pathways include fuel or oil releases, vessel "
                "activity, urban runoff, and combustion-related residues.",
                "The pattern of compounds, sampling conditions, and local "
                "activity records are needed to investigate the source."
            ],
            "precautions": [
                "Where relevant, review port, marina, stormwater, and "
                "spill-report information for the sampling area.",
                "Use the appropriate analytical method to confirm the "
                "substance and concentration.",
                "If a release is suspected, follow local spill-response "
                "instructions and avoid contact with affected material."
            ]
        }

    if any(term in label for term in [
        "microplastic", "plastic", "polyethylene",
        "polypropylene", "polymer"
    ]):
        return {
            "category": "Plastic-related pollutant",
            "causes": [
                "Potential pathways include litter, wastewater, stormwater, "
                "lost fishing gear, and the breakdown of larger plastic items.",
                "Particle type, size, sampling method, and contamination "
                "controls are important when interpreting microplastic data."
            ],
            "precautions": [
                "Investigate local litter, wastewater, drainage, and "
                "fishing-related pathways where relevant.",
                "Reduce waste entering drains and waterways.",
                "Use consistent sampling and contamination-control methods "
                "when comparing particle counts."
            ]
        }

    if any(term in label for term in [
        "pesticide", "herbicide", "insecticide"
    ]):
        return {
            "category": "Agricultural or industrial chemical",
            "causes": [
                "Possible pathways include agricultural runoff, landscape "
                "maintenance, wastewater, and improper chemical disposal.",
                "The exact substance matters: different chemicals have "
                "different uses, persistence, and environmental behaviour."
            ],
            "precautions": [
                "Identify the specific chemical rather than relying only "
                "on a broad label.",
                "Investigate relevant land use, runoff, and chemical-use "
                "records around the sampling area.",
                "Confirm the result before selecting a treatment or "
                "remediation method."
            ]
        }

    if any(term in label for term in [
        "nitrogen", "nitrate", "nitrite", "ammonia", "phosphate", "phosphorus"
    ]):
        return {
            "category": "Nutrient",
            "causes": [
                "Possible nutrient pathways include wastewater, agricultural "
                "runoff, stormwater, and decomposition of organic material.",
                "Excess nutrients can contribute to algal growth in suitable "
                "conditions, but a nutrient measurement alone does not prove "
                "that an algal bloom or ecological impact occurred."
            ],
            "precautions": [
                "Review wastewater and stormwater pathways and nearby "
                "land-use information.",
                "Interpret the result alongside dissolved oxygen, water "
                "conditions, season, and compatible historical measurements.",
                "Investigate repeated elevated measurements rather than "
                "treating one record as proof of eutrophication."
            ]
        }

    if any(term in label for term in [
        "bacteria", "enterococcus", "e. coli", "coliform", "pathogen"
    ]):
        return {
            "category": "Microbiological indicator",
            "causes": [
                "Possible pathways include wastewater leakage, sewage "
                "overflows, animal waste, and contaminated stormwater.",
                "The indicator measured and the method used determine "
                "what the result can tell us about contamination."
            ],
            "precautions": [
                "Check official beach or water-quality advisories.",
                "Investigate wastewater and stormwater pathways if repeated "
                "results warrant it.",
                "Follow the applicable health guidance; do not infer safety "
                "from a single result."
            ]
        }

    return {
        "category": "Specific contaminant",
        "causes": [
            "The parameter label does not provide enough evidence to identify "
            "a source. Possible pathways depend on the substance, local "
            "activities, sample matrix, and environmental conditions.",
            "Use the full parameter name, analytical method, and local "
            "environmental records to develop more specific hypotheses."
        ],
        "precautions": [
            "Verify the parameter identity, unit, qualifier, and detection limit.",
            "Investigate plausible local sources using independent evidence.",
            "Repeat comparable measurements before assessing trends or "
            "recommending site-specific remediation."
        ]
    }


# ==================================================
# LOCATION-SPECIFIC DATA SUMMARY
# ==================================================

def build_location_insight(records, location, pollutant):
    """
    Summarizes what the selected location's records actually show.
    It does not claim that the location caused the measured pollution.
    """
    if not location:
        return {
            "heading": "Location-level interpretation",
            "text": (
                "Select a sampling location to get a location-specific "
                "summary. With all locations selected, the results combine "
                "different sampling areas and may hide local differences."
            ),
            "comparison": (
                "Choose a pollutant and location to compare compatible "
                "measurements against other sampled locations."
            )
        }

    if not records:
        return {
            "heading": f"Data for {location}",
            "text": (
                "No records match this location and the current filters. "
                "Try clearing the year filter or selecting another pollutant."
            ),
            "comparison": (
                "There are no matching records available for a reliable "
                "location-level comparison."
            )
        }

    values = []
    non_detect_count = 0
    qualified_count = 0
    unqualified_count = 0
    years = set()
    units = set()
    matrices = set()

    for row in records:
        qualifier = clean_text(row.get("qualifier"))
        value = as_number(row.get("value"))

        if is_non_detect(qualifier):
            non_detect_count += 1
        elif qualifier and value is not None:
            qualified_count += 1
        elif value is not None:
            unqualified_count += 1

        if value is not None and not is_non_detect(qualifier):
            values.append(value)

        if row.get("fiscal_year") is not None:
            years.add(str(row["fiscal_year"]))

        if clean_text(row.get("unit")):
            units.add(clean_text(row.get("unit")))

        if clean_text(row.get("matrix")):
            matrices.add(clean_text(row.get("matrix")))

    text = (
        f"The selected location, {location}, has {len(records)} matching "
        f"records for the current filters. "
        f"{non_detect_count} are labelled non-detect, "
        f"{qualified_count} have a qualifier and a numeric value, and "
        f"{unqualified_count} have a numeric value without a recorded "
        f"qualifier."
    )

    if values:
        text += (
            f" Among numeric values not labelled non-detect, the observed "
            f"range is {min(values):.6g} to {max(values):.6g}."
        )
    else:
        text += (
            " There are no usable numeric detected values for a simple "
            "range summary."
        )

    if years:
        text += (
            " Years represented: "
            + ", ".join(sorted(years))
            + "."
        )

    if len(units) > 1:
        text += (
            " Multiple units occur in these records, so the numeric range "
            "must not be treated as one directly comparable series."
        )

    if len(matrices) > 1:
        text += (
            " Multiple sample matrices occur in these records; compare "
            "like with like before interpreting the range."
        )

    comparison = (
        "These figures describe the available records, not the cause "
        "of contamination or the severity of ecological damage."
    )

    if pollutant:
        comparison += (
            f" The selected parameter is {pollutant}. Use the historical "
            "trend section to check whether enough comparable years are "
            "available for an exploratory estimate."
        )

    return {
        "heading": f"Observed data at {location}",
        "text": text,
        "comparison": comparison
    }


# ==================================================
# HISTORICAL TREND / EXPLORATORY FORECAST
# ==================================================

def calculate_forecast(records):
    """
    Calculates a simple linear trend using yearly averages, separated
    by unit and sample matrix. Requires at least three different years.
    This is exploratory, not a validated environmental prediction.
    """
    grouped = defaultdict(list)

    for row in records:
        year = row.get("fiscal_year")
        value = as_number(row.get("value"))
        unit = clean_text(row.get("unit"))
        matrix = clean_text(row.get("matrix")).lower()

        if year is None or value is None or not unit:
            continue

        if is_non_detect(row.get("qualifier")):
            continue

        try:
            numeric_year = int(year)
        except (TypeError, ValueError):
            continue

        grouped[(unit, matrix)].append((numeric_year, value))

    candidates = []

    for (unit, matrix), observations in grouped.items():
        yearly_values = defaultdict(list)

        for year, value in observations:
            yearly_values[year].append(value)

        points = [
            (year, mean(values))
            for year, values in sorted(yearly_values.items())
        ]

        if len(points) >= 3:
            candidates.append((len(points), unit, matrix, points))

    if not candidates:
        return {
            "available": False,
            "message": (
                "There are not enough comparable detected measurements "
                "across at least three different years for a trend estimate. "
                "Try clearing the year filter or broadening the other filters. "
                "The system will not invent a prediction when the data is "
                "insufficient."
            )
        }

    candidates.sort(key=lambda item: item[0], reverse=True)
    _, unit, matrix, points = candidates[0]

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]

    x_mean = mean(xs)
    y_mean = mean(ys)

    denominator = sum((x - x_mean) ** 2 for x in xs)

    if denominator == 0:
        return {
            "available": False,
            "message": "The available years do not support a trend estimate."
        }

    slope = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(xs, ys)
    ) / denominator

    intercept = y_mean - slope * x_mean
    next_year = max(xs) + 1
    estimate = intercept + slope * next_year

    direction = (
        "increasing" if slope > 0
        else "decreasing" if slope < 0
        else "approximately stable"
    )

    # Do not force a negative mathematical estimate to zero silently.
    # Instead, disclose that a negative estimate is not physically
    # interpretable as a concentration.
    if estimate < 0:
        return {
            "available": False,
            "message": (
                "The fitted line produces a negative next-year estimate, "
                "which is not meaningful for a concentration. A linear "
                "forecast is unsuitable for this series; inspect the "
                "historical measurements instead."
            )
        }

    return {
        "available": True,
        "next_year": next_year,
        "estimate": round(estimate, 6),
        "unit": unit,
        "matrix": matrix or "not specified",
        "direction": direction,
        "years_used": len(points),
        "first_year": min(xs),
        "last_year": max(xs),
        "message": (
            "This estimate extends a straight-line fit to historical yearly "
            "averages. It does not account for seasonal variation, sampling "
            "changes, environmental events, or future interventions. It is "
            "not a validated environmental forecast."
        )
    }


# ==================================================
# MAIN DASHBOARD
# ==================================================

@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM noaa_pollution_data"
        )
        total_records = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM pollutants"
        )
        total_pollutants = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(DISTINCT specific_location) AS total
            FROM noaa_pollution_data
            WHERE specific_location IS NOT NULL
              AND specific_location <> ''
        """)
        total_locations = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT p.pollutant_name,
                   COUNT(pm.measurement_id) AS measurement_count
            FROM pollutants p
            LEFT JOIN pollution_measurements pm
                ON p.pollutant_id = pm.pollutant_id
            GROUP BY p.pollutant_id, p.pollutant_name
            ORDER BY measurement_count DESC
        """)
        pollutant_data = cursor.fetchall()

        return render_template(
            "index.html",
            total_records=total_records,
            total_pollutants=total_pollutants,
            total_locations=total_locations,
            pollutant_data=pollutant_data
        )
    finally:
        cursor.close()
        conn.close()


# ==================================================
# EXPLORE DATA
# ==================================================

@app.route("/explore")
def explore():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        pollutant = request.args.get("pollutant", "").strip()
        location = request.args.get("location", "").strip()
        year = read_valid_year(request.args.get("year", "").strip())

        cursor.execute("""
            SELECT DISTINCT parameter
            FROM noaa_pollution_data
            WHERE parameter IS NOT NULL AND parameter <> ''
            ORDER BY parameter
        """)
        pollutants = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT specific_location
            FROM noaa_pollution_data
            WHERE specific_location IS NOT NULL
              AND specific_location <> ''
            ORDER BY specific_location
        """)
        locations = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT fiscal_year
            FROM noaa_pollution_data
            WHERE fiscal_year IS NOT NULL
            ORDER BY fiscal_year DESC
        """)
        years = cursor.fetchall()

        query = """
            SELECT object_id, collection_date, specific_location,
                   scientific_name, parameter, value, unit,
                   qualifier, detection_limit, fiscal_year
            FROM noaa_pollution_data
            WHERE 1 = 1
        """
        params = []

        if pollutant:
            query += " AND parameter = %s"
            params.append(pollutant)

        if location:
            query += " AND specific_location = %s"
            params.append(location)

        if year:
            query += " AND fiscal_year = %s"
            params.append(int(year))

        query += """
            ORDER BY collection_date DESC, object_id DESC
            LIMIT 200
        """

        cursor.execute(query, tuple(params))
        records = cursor.fetchall()

        return render_template(
            "explore.html",
            pollutants=pollutants,
            locations=locations,
            years=years,
            records=records,
            selected_pollutant=pollutant,
            selected_location=location,
            selected_year=year
        )
    finally:
        cursor.close()
        conn.close()


# ==================================================
# ANALYTICS, INSIGHTS, PRECAUTIONS AND FORECAST
# ==================================================

@app.route("/analytics")
def analytics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        pollutant = request.args.get("pollutant", "").strip()
        location = request.args.get("location", "").strip()
        year = read_valid_year(request.args.get("year", "").strip())

        # Dropdown options
        cursor.execute("""
            SELECT DISTINCT parameter
            FROM noaa_pollution_data
            WHERE parameter IS NOT NULL AND parameter <> ''
            ORDER BY parameter
        """)
        pollutants = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT specific_location
            FROM noaa_pollution_data
            WHERE specific_location IS NOT NULL
              AND specific_location <> ''
            ORDER BY specific_location
        """)
        locations = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT fiscal_year
            FROM noaa_pollution_data
            WHERE fiscal_year IS NOT NULL
            ORDER BY fiscal_year DESC
        """)
        years = cursor.fetchall()

        # Build the filter for charts and selected records.
        where_clause = " WHERE 1 = 1"
        params = []

        if pollutant:
            where_clause += " AND parameter = %s"
            params.append(pollutant)

        if location:
            where_clause += " AND specific_location = %s"
            params.append(location)

        if year:
            where_clause += " AND fiscal_year = %s"
            params.append(int(year))

        # Records by year
        cursor.execute("""
            SELECT fiscal_year, COUNT(*) AS total
            FROM noaa_pollution_data
        """ + where_clause + """
            AND fiscal_year IS NOT NULL
            GROUP BY fiscal_year
            ORDER BY fiscal_year
        """, tuple(params))
        year_data = cursor.fetchall()

        # Top locations
        cursor.execute("""
            SELECT specific_location, COUNT(*) AS total
            FROM noaa_pollution_data
        """ + where_clause + """
            AND specific_location IS NOT NULL
            AND specific_location <> ''
            GROUP BY specific_location
            ORDER BY total DESC, specific_location
            LIMIT 10
        """, tuple(params))
        location_data = cursor.fetchall()

        # Records by parameter
        cursor.execute("""
            SELECT parameter, COUNT(*) AS total
            FROM noaa_pollution_data
        """ + where_clause + """
            AND parameter IS NOT NULL AND parameter <> ''
            GROUP BY parameter
            ORDER BY total DESC, parameter
        """, tuple(params))
        pollutant_counts = cursor.fetchall()

        # Full set matching the selected filters.
        cursor.execute("""
            SELECT object_id, parameter, specific_location,
                   fiscal_year, collection_date, value, unit,
                   qualifier, detection_limit, matrix, method
            FROM noaa_pollution_data
        """ + where_clause + """
            ORDER BY collection_date, object_id
        """, tuple(params))
        selected_records = cursor.fetchall()

        # A separate historical series deliberately ignores the year filter.
        # It still respects the selected pollutant and location.
        trend_clause = " WHERE 1 = 1"
        trend_params = []

        if pollutant:
            trend_clause += " AND parameter = %s"
            trend_params.append(pollutant)

        if location:
            trend_clause += " AND specific_location = %s"
            trend_params.append(location)

        cursor.execute("""
            SELECT object_id, parameter, specific_location,
                   fiscal_year, collection_date, value, unit,
                   qualifier, detection_limit, matrix, method
            FROM noaa_pollution_data
        """ + trend_clause + """
            ORDER BY fiscal_year, collection_date, object_id
        """, tuple(trend_params))
        trend_records = cursor.fetchall()

        total_selected = len(selected_records)
        detected_count = 0
        not_detected_count = 0
        other_qualifier_count = 0
        numeric_values = []

        for row in selected_records:
            qualifier = clean_text(row.get("qualifier"))
            value = as_number(row.get("value"))

            if is_non_detect(qualifier):
                not_detected_count += 1
            elif value is not None and qualifier:
                detected_count += 1
            elif value is not None:
                other_qualifier_count += 1

            if value is not None:
                numeric_values.append(value)

        # Pollutant-level source hypotheses and precautions.
        guidance = pollutant_guidance(pollutant)

        if pollutant:
            cause_heading = (
                f"Possible sources for {pollutant} — not confirmed causes"
            )
            cause_text = " ".join(guidance["causes"])
            precautions = guidance["precautions"]
        else:
            cause_heading = "Possible causes to investigate"
            cause_text = (
                "The current selection includes multiple pollutant types. "
                "Their sources and environmental behaviour differ, so a "
                "single cause statement would be misleading. Select a "
                "pollutant for more specific educational guidance."
            )
            precautions = [
                "Review each parameter's identity, units, qualifier, "
                "detection limit, and sample matrix.",
                "Investigate possible sources using local discharge records, "
                "land use, and other independent evidence.",
                "Compare compatible measurements and repeat sampling "
                "before drawing conclusions."
            ]

        # Data-driven conclusion for selected filters.
        if total_selected == 0:
            conclusion = (
                "No records match the selected filters. Clear or change "
                "the filters to inspect available records."
            )
        else:
            conclusion = (
                f"The selected filters match {total_selected} records. "
                f"{not_detected_count} are labelled non-detect, "
                f"{detected_count} have a qualifier and numeric value, "
                f"and {other_qualifier_count} have a numeric value without "
                f"a recorded qualifier. These are record counts, not a "
                f"measure of pollution severity."
            )

        # Summary for the selected sampling location.
        location_insight = build_location_insight(
            selected_records, location, pollutant
        )

        # A forecast is calculated from the historical series, not from
        # a single year selected in the filter.
        forecast = calculate_forecast(trend_records)

        # Numeric range summary for current filters.
        if numeric_values:
            value_summary = {
                "count": len(numeric_values),
                "minimum": round(min(numeric_values), 6),
                "maximum": round(max(numeric_values), 6),
                "median": round(median(numeric_values), 6)
            }
        else:
            value_summary = None

        return render_template(
            "analytics.html",
            year_data=year_data,
            location_data=location_data,
            pollutant_counts=pollutant_counts,
            pollutants=pollutants,
            locations=locations,
            years=years,
            selected_pollutant=pollutant,
            selected_location=location,
            selected_year=year,
            total_selected=total_selected,
            detected_count=detected_count,
            not_detected_count=not_detected_count,
            other_qualifier_count=other_qualifier_count,
            cause_heading=cause_heading,
            cause_text=cause_text,
            precautions=precautions,
            conclusion=conclusion,
            location_insight=location_insight,
            forecast=forecast,
            value_summary=value_summary
        )
    finally:
        cursor.close()
        conn.close()


# ==================================================
# POLLUTION MAP
# ==================================================

@app.route("/map")
def pollution_map():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        pollutant = request.args.get("pollutant", "").strip()
        location = request.args.get("location", "").strip()
        year = read_valid_year(request.args.get("year", "").strip())

        cursor.execute("""
            SELECT DISTINCT parameter
            FROM noaa_pollution_data
            WHERE parameter IS NOT NULL AND parameter <> ''
            ORDER BY parameter
        """)
        pollutants = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT specific_location
            FROM noaa_pollution_data
            WHERE specific_location IS NOT NULL
              AND specific_location <> ''
            ORDER BY specific_location
        """)
        locations = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT fiscal_year
            FROM noaa_pollution_data
            WHERE fiscal_year IS NOT NULL
            ORDER BY fiscal_year DESC
        """)
        years = cursor.fetchall()

        query = """
            SELECT object_id, specific_location, latitude, longitude,
                   parameter, value, unit, qualifier, collection_date,
                   detection_limit, fiscal_year
            FROM noaa_pollution_data
            WHERE latitude BETWEEN -90 AND 90
              AND longitude BETWEEN -180 AND 180
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
        """
        params = []

        if pollutant:
            query += " AND parameter = %s"
            params.append(pollutant)

        if location:
            query += " AND specific_location = %s"
            params.append(location)

        if year:
            query += " AND fiscal_year = %s"
            params.append(int(year))

        query += " ORDER BY object_id LIMIT 5000"

        cursor.execute(query, tuple(params))
        map_records = cursor.fetchall()

        return render_template(
            "map.html",
            map_records=map_records,
            pollutants=pollutants,
            locations=locations,
            years=years,
            selected_pollutant=pollutant,
            selected_location=location,
            selected_year=year
        )
    finally:
        cursor.close()
        conn.close()


# ==================================================
# ADMIN LOGIN
# ==================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        app.logger.warning("ADMIN LOGIN POST RECEIVED")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT admin_id, username, password_hash
                FROM admin_users
                WHERE username = %s
            """, (username,))
            admin = cursor.fetchone()

            if admin and check_password_hash(
                admin["password_hash"], password
            ):
                session.clear()
                session["admin_id"] = admin["admin_id"]
                session["admin_username"] = admin["username"]

                try:
                    write_audit_log(
                        cursor, "LOGIN", "Administrator logged in"
                    )
                    conn.commit()
                    app.logger.warning("LOGIN AUDIT COMMIT COMPLETED")
                except Exception:
                    conn.rollback()
                    app.logger.exception(
                        "Could not save login audit log"
                    )

                flash("Login successful.", "success")
                return redirect(url_for("admin_dashboard"))

            flash("Invalid username or password.", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template("admin_login.html")


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM admin_users")
        total_admins = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM pollutants")
        total_pollutants = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM audit_logs")
        total_logs = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT log_id, action, details, created_at
            FROM audit_logs
            WHERE admin_id = %s
            ORDER BY created_at DESC, log_id DESC
            LIMIT 10
        """, (session["admin_id"],))

        recent_logs = cursor.fetchall()

        return render_template(
            "admin_dashboard.html",
            total_admins=total_admins,
            total_pollutants=total_pollutants,
            total_logs=total_logs,
            recent_logs=recent_logs
        )
    finally:
        cursor.close()
        conn.close()



# ==================================================
# POLLUTANT MANAGEMENT
# ==================================================

@app.route("/admin/pollutants", methods=["GET", "POST"])
@admin_required
def admin_pollutants():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == "POST":
            name = request.form.get("pollutant_name", "").strip()
            group = request.form.get("pollutant_group", "").strip()

            if not name:
                flash("Pollutant name is required.", "error")
            elif len(name) > 150 or len(group) > 100:
                flash("The supplied text is too long.", "error")
            else:
                try:
                    cursor.execute("""
                        INSERT INTO pollutants
                            (pollutant_name, pollutant_group)
                        VALUES (%s, %s)
                    """, (name, group or None))

                    write_audit_log(
                        cursor, "ADD_POLLUTANT",
                        "Added pollutant: " + name
                    )
                    conn.commit()
                    flash("Pollutant added successfully.", "success")

                except Exception as error:
                    conn.rollback()

                    if getattr(error, "errno", None) == 1062:
                        flash("That pollutant already exists.", "error")
                    else:
                        app.logger.exception("Pollutant insert failed")
                        flash("Could not add the pollutant.", "error")

                return redirect(url_for("admin_pollutants"))

        cursor.execute("""
            SELECT pollutant_id, pollutant_name, pollutant_group
            FROM pollutants
            ORDER BY pollutant_name
        """)
        pollutants = cursor.fetchall()

        return render_template(
            "admin_pollutants.html",
            pollutants=pollutants
        )
    finally:
        cursor.close()
        conn.close()


# ==================================================
# AUDIT LOGS
# ==================================================

@app.route("/admin/audit-logs")
@admin_required
def admin_audit_logs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT l.log_id, l.action, l.details, l.created_at,
                   u.username
            FROM audit_logs l
            LEFT JOIN admin_users u ON l.admin_id = u.admin_id
            ORDER BY l.created_at DESC, l.log_id DESC
            LIMIT 200
        """)
        logs = cursor.fetchall()

        return render_template(
            "admin_audit_logs.html",
            logs=logs
        )
    finally:
        cursor.close()
        conn.close()


# ==================================================
# ADMIN LOGOUT
# ==================================================

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    app.logger.warning("ADMIN LOGOUT ROUTE RECEIVED")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        write_audit_log(
            cursor, "LOGOUT", "Administrator logged out"
        )
        conn.commit()
        app.logger.warning("LOGOUT AUDIT COMMIT COMPLETED")
    except Exception:
        conn.rollback()
        app.logger.exception("Could not save logout audit log")
    finally:
        cursor.close()
        conn.close()

    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
   app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")