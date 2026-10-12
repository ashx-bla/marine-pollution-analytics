import csv
import os
import mysql.connector

file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "noaa_pollution_expanded.csv"
)

con = None
cursor = None

try:
    # Connect using environment variables
    con = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "marine_pollution_db")
    )

    cursor = con.cursor()

    # Read CSV file
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    print("CSV records found:", len(rows))

    # Get IDs already present in the database
    cursor.execute("SELECT object_id FROM noaa_pollution_data")
    existing_ids = {row[0] for row in cursor.fetchall()}

    # MySQL table column order
    columns = [
        "object_id", "study", "study_type", "site_id", "sample_id",
        "general_location", "specific_location", "region", "state",
        "latitude", "longitude", "collaborator", "fiscal_year",
        "collection_date", "matrix", "scientific_name", "parameter_code",
        "parameter", "value", "qualifier", "unit", "method_blank",
        "detection_limit", "method", "laboratory",
        "cpde_search_engine_group", "x", "y"
    ]

    sql = """
        INSERT INTO noaa_pollution_data (
            object_id, study, study_type, site_id, sample_id,
            general_location, specific_location, region, state,
            latitude, longitude, collaborator, fiscal_year,
            collection_date, matrix, scientific_name, parameter_code,
            parameter, value, qualifier, unit, method_blank,
            detection_limit, method, laboratory,
            cpde_search_engine_group, x, y
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    new_rows = []

    for row in rows:
        object_id = int(row["OBJECTID"])

        # Skip records already imported
        if object_id in existing_ids:
            continue

        values = []

        for col in columns:
            value = (
                row["OBJECTID"]
                if col == "object_id"
                else row[col]
            )

            if value is not None:
                value = value.strip()

            if value == "":
                value = None

            values.append(value)

        new_rows.append(tuple(values))
        existing_ids.add(object_id)

    print("New records to import:", len(new_rows))

    # Import records in a transaction
    if new_rows:
        cursor.executemany(sql, new_rows)

    con.commit()

    # Show final database count
    cursor.execute("SELECT COUNT(*) FROM noaa_pollution_data")
    total_records = cursor.fetchone()[0]

    print("New records imported:", len(new_rows))
    print("Total records in database:", total_records)

except Exception as e:
    if con is not None and con.is_connected():
        con.rollback()

    print("Import failed:", e)

finally:
    if cursor is not None:
        cursor.close()

    if con is not None and con.is_connected():
        con.close()