from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import io
import Extracting_prescription_data
import traceback
from fastapi.middleware.cors import CORSMiddleware
import json
import re
import Critical_Warinings
import SQLLITE3_DataBase
from AI_assistant_logic import MedicalAssistant
import logging
import os

# --- Logging Setup (readable in Render dashboard) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MediGrid")

api = FastAPI()

# --- 1. Root Endpoint ---
@api.get("/")
async def read_root():
    return FileResponse('static/test1.html')

# --- Initialize AI ---
logger.info("Initializing AI assistant...")
ai_bot = MedicalAssistant()
logger.info("AI assistant ready.")

class MedicationItem(BaseModel):
    medications: str
    Dosage: str
    Frequency: str
    Duration: str
    Map_link: str 

class PrescriptionRequest(BaseModel):
    Prescription_info: List[MedicationItem]

class ChatRequest(BaseModel):
    message: str


api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- 2. Prescription Extraction Endpoint ---
@api.post('/data_extraction')
async def prescription_dataExtraction(
    image: UploadFile = File(...),
    user_location: Optional[str] = Form(None) 
):
    logger.info(f"[/data_extraction] Request received | file={image.filename} | size~={image.size}B")
    try:
        content = await image.read()
        img_byte = io.BytesIO(content)
        
        loc_data_dict = None
        if user_location:
            try:
                loc_data_dict = json.loads(user_location)
                logger.info(f"[/data_extraction] Location received: {loc_data_dict}")
            except Exception as e:
                logger.warning(f"[/data_extraction] Failed to parse location: {e}")

        obj = Extracting_prescription_data.Handwritting_Extraction()
        
        try:
            result = obj.extracting_presc_data(img_byte, loc_data_dict)
            
            response = ''
            for chunk in result:
                if chunk.parts:
                    response += chunk.text
            
            match = re.search(r'(\{.*\})', response, re.DOTALL)
            clean_json = match.group(1) if match else response
            data = json.loads(clean_json)

            med_count = len(data.get("Prescription_info", []))
            logger.info(f"[/data_extraction] SUCCESS — {med_count} medication(s) extracted.")
            return data
            
        except Exception as gemini_error:
            error_str = str(gemini_error).lower()
            if "quota exceeded" in error_str or "429" in error_str or "rate limit" in error_str:
                logger.error(f"[/data_extraction] GEMINI QUOTA ERROR: {gemini_error}")
                return {
                    "patient_info": {},
                    "Prescription_info": [],
                    "error": "API quota exceeded. Please try again tomorrow or upgrade plan."
                }
            else:
                logger.error(f"[/data_extraction] GEMINI ERROR: {gemini_error}")
                traceback.print_exc()
                return {
                    "patient_info": {},
                    "Prescription_info": [],
                    "error": "Failed to analyze prescription. Please try again with a clearer image."
                }

    except Exception as e:
        logger.error(f"[/data_extraction] UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return {
            "patient_info": {},
            "Prescription_info": [],
            "error": "An error occurred during processing. Please try again."
        }

@api.post('/critical_warnings', response_model=None)
async def critical_warnings_handler(extracted_data: PrescriptionRequest):
    logger.info("[/critical_warnings] Request received.")
    try:
        warn_obj = Critical_Warinings.warnings()
        warn_response = warn_obj.analyzing_critical_warnings(extracted_data.model_dump())
        logger.info(f"[/critical_warnings] SUCCESS — {len(warn_response)} warning(s) returned.")
        return warn_response
    except Exception as e:
        logger.error(f"[/critical_warnings] ERROR: {e}")
        return []

@api.post('/post_into_db')
def save_to_sql(payload: dict):
    logger.info("[/post_into_db] Saving record to database.")
    try:
        sql_obj = SQLLITE3_DataBase.medi_data_base()
        result = sql_obj.save_to_db(payload)
        logger.info("[/post_into_db] SUCCESS — record saved.")
        return result
    except Exception as e:
        logger.error(f"[/post_into_db] ERROR: {e}")
        raise HTTPException(status_code=500, detail="Database save failed.")

@api.get('/get_Saved_data')
def get_saved_details():
    logger.info("[/get_Saved_data] Fetching history.")
    try:
        sql_obj = SQLLITE3_DataBase.medi_data_base()
        result = sql_obj.display_table()
        records = result.to_dict(orient='records')
        logger.info(f"[/get_Saved_data] SUCCESS — {len(records)} record(s) returned.")
        return records
    except Exception as e:
        logger.error(f"[/get_Saved_data] ERROR: {e}")
        return []

@api.post("/chat")
async def chat_endpoint(request: dict):
    message = request.get("message", "").strip()
    logger.info(f"[/chat] Request received | msg_len={len(message)}")
    try:
        if not message:
            return {"response": "Empty message."}

        response_text = ai_bot.process_chat(message, session_key="default_user")
        logger.info("[/chat] SUCCESS — response sent.")
        return {"response": str(response_text)}

    except Exception as e:
        logger.error(f"[/chat] ERROR: {e}")
        return {"response": "AI service temporarily unavailable."}

# --- Mount Static Files (Catch-all for frontend) ---
api.mount("/", StaticFiles(directory="static", html=True), name="static")

app = api

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fast_api_file:app", host="0.0.0.0", port=8000)

