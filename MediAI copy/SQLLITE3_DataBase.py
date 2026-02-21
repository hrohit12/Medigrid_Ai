import sqlite3
import pandas as pd
from datetime import datetime

# --- Safe DB columns (used for empty-state fallback) ---
_PRESCRIPTION_COLUMNS = [
    'PATIENT_NAME', 'MEDICATION_NAME', 'DOSAGE',
    'FREQUENCY', 'DURATION', 'MAP_LINK', 'Data_Saved'
]

def initialize_db():
    """Create MediGrid.db and required tables if they do not exist.
    Called once at module load so the app never crashes on first deployment.
    """
    try:
        conn = sqlite3.connect('MediGrid.db')
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Prescription (
                PATIENT_NAME  TEXT,
                MEDICATION_NAME TEXT,
                DOSAGE        TEXT,
                FREQUENCY     TEXT,
                DURATION      TEXT,
                MAP_LINK      TEXT,
                Data_Saved    DATETIME
            )
        """)
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Run once when the module is imported
initialize_db()

class medi_data_base():
    # function for establishing the connection with database
    def get_db_connection(self):
        return sqlite3.connect('MediGrid.db')

    #fuction for saving the data with dynamic table creation.
    def save_to_db(self,full_data):

        p_info = full_data.get('patient_info', {})
        raw_name = p_info.get("patient_name") or p_info.get("Name") or "Unknown_Patient"
        patient_name = str(raw_name)
        up_patient_name = patient_name.replace(' ', '_')
        

        local_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        connection=self.get_db_connection()
        c=connection.cursor()

        patient_table=f"""
        CREATE TABLE IF NOT EXISTS Prescription (
        PATIENT_NAME text,
        MEDICATION_NAME text,
        DOSAGE text,
        FREQUENCY text,
        DURATION text,
        MAP_LINK text,
        Data_Saved DATETIME 
        )"""

        c.execute(patient_table)

        presc_list = full_data.get('Prescription_info') or full_data.get('prescription_info') or []

        for item in presc_list:

            inserting_details=f"""
            INSERT INTO Prescription (PATIENT_NAME,MEDICATION_NAME,DOSAGE,FREQUENCY,DURATION,MAP_LINK,Data_Saved)
            VALUES(?,?,?,?,?,?,?)"""

            c.execute(inserting_details,(patient_name,item.get("medications", "Not provided"),
                item.get("Dosage", "Not provided"),
                item.get("Frequency", "Not provided"),
                item.get("Duration", "Not provided"),
                item.get("Map_link", "Not provided"),
                local_time
            ))
        connection.commit()
        connection.close()
        return 'Saved_Successfully'


    # this fuction will displays the entire table
    def display_table(self):
        connection = self.get_db_connection()
        try:
            data = pd.read_sql_query(
                'SELECT * FROM Prescription ORDER BY Data_Saved DESC', connection
            )

            # Return empty DataFrame with correct columns if no rows
            if data.empty:
                return pd.DataFrame(columns=_PRESCRIPTION_COLUMNS)

            display_rows = []
            previous_timeStamp = None
            for index, row in data.iterrows():
                current_timeStamp = row['Data_Saved']

                if previous_timeStamp is not None and current_timeStamp != previous_timeStamp:
                    empty_row = {col: '' for col in data.columns}
                    display_rows.append(empty_row)

                display_rows.append(row.to_dict())
                previous_timeStamp = current_timeStamp

            return pd.DataFrame(display_rows)

        except Exception as e:
            print(f"display_table error: {e}")
            return pd.DataFrame(columns=_PRESCRIPTION_COLUMNS)
        finally:
            connection.close()
        

    