from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# -------------------- DATA --------------------

doctors = [
    {"id": 1, "name": "siva", "specialization": "Cardiologist", "fee": 500, "experience_years": 10, "is_available": True},
    {"id": 2, "name": "Suresh", "specialization": "Dermatologist", "fee": 300, "experience_years": 5, "is_available": True},
    {"id": 3, "name": "hari", "specialization": "Pediatrician", "fee": 600, "experience_years": 8, "is_available": False},
    {"id": 4, "name": "shanthi", "specialization": "General", "fee": 300, "experience_years": 3, "is_available": True},
    {"id": 5, "name": "ravi", "specialization": "Cardiologist", "fee": 1000, "experience_years": 12, "is_available": True},
    {"id": 6, "name": "rahul", "specialization": "Dermatologist", "fee": 500, "experience_years": 6, "is_available": True},
]

appointments = []
appt_counter = 1

# -------------------- MODELS --------------------

class AppointmentRequest(BaseModel):
    patient_name: str = Field(min_length=2)
    doctor_id: int = Field(gt=0)
    date: str = Field(min_length=8)
    reason: str = Field(min_length=5)
    appointment_type: str = "in-person"
    senior_citizen: bool = False

class NewDoctor(BaseModel):
    name: str = Field(min_length=2)
    specialization: str = Field(min_length=2)
    fee: int = Field(gt=0)
    experience_years: int = Field(gt=0)
    is_available: bool = True

# -------------------- HELPERS --------------------

def find_doctor(doc_id):
    for d in doctors:
        if d["id"] == doc_id:
            return d
    return None

def calculate_fee(base_fee, appointment_type, senior):
    if appointment_type == "video":
        fee = base_fee * 0.8
    elif appointment_type == "emergency":
        fee = base_fee * 1.5
    else:
        fee = base_fee

    original_fee = fee

    if senior:
        fee = fee * 0.85

    return original_fee, fee

def filter_doctors_logic(specialization, max_fee, min_exp, is_available):
    result = doctors
    if specialization is not None:
        result = [d for d in result if d["specialization"].lower() == specialization.lower()]
    if max_fee is not None:
        result = [d for d in result if d["fee"] <= max_fee]
    if min_exp is not None:
        result = [d for d in result if d["experience_years"] >= min_exp]
    if is_available is not None:
        result = [d for d in result if d["is_available"] == is_available]
    return result

# -------------------- DAY 1 --------------------

@app.get("/")
def home():
    return {"message": "Welcome to MediCare Clinic"}

@app.get("/doctors")
def get_doctors():
    available = sum(1 for d in doctors if d["is_available"])
    return {
        "total": len(doctors),
        "available_count": available,
        "data": doctors
    }

@app.get("/appointments")
def get_appointments():
    return {"total": len(appointments), "data": appointments}

@app.get("/doctors/summary")
def summary():
    most_exp = max(doctors, key=lambda x: x["experience_years"])
    cheapest = min(doctors, key=lambda x: x["fee"])

    spec_count = {}
    for d in doctors:
        spec = d["specialization"]
        spec_count[spec] = spec_count.get(spec, 0) + 1

    return {
        "total_doctors": len(doctors),
        "available": sum(d["is_available"] for d in doctors),
        "most_experienced": most_exp["name"],
        "cheapest_fee": cheapest["fee"],
        "specialization_count": spec_count
    }

# -------------------- FILTER --------------------

@app.get("/doctors/filter")
def filter_doctors(
    specialization: Optional[str] = Query(None),
    max_fee: Optional[int] = Query(None),
    min_experience: Optional[int] = Query(None),
    is_available: Optional[bool] = Query(None)
):
    return filter_doctors_logic(specialization, max_fee, min_experience, is_available)

# -------------------- SEARCH --------------------

@app.get("/doctors/search")
def search(keyword: str):
    result = [d for d in doctors if keyword.lower() in d["name"].lower() or keyword.lower() in d["specialization"].lower()]
    if not result:
        return {"message": "No doctors found"}
    return {"total_found": len(result), "data": result}

# -------------------- SORT --------------------

@app.get("/doctors/sort")
def sort(sort_by: str = "fee", order: str = "asc"):
    if sort_by not in ["fee", "name", "experience_years"]:
        raise HTTPException(400, "Invalid sort field")
    reverse = True if order == "desc" else False
    sorted_data = sorted(doctors, key=lambda x: x[sort_by], reverse=reverse)
    return {"sorted_by": sort_by, "order": order, "data": sorted_data}

# -------------------- PAGINATION --------------------

@app.get("/doctors/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit
    total_pages = math.ceil(len(doctors) / limit)
    return {"page": page, "total_pages": total_pages, "data": doctors[start:end]}

# -------------------- CRUD --------------------

@app.post("/doctors", status_code=201)
def add_doctor(doc: NewDoctor):
    for d in doctors:
        if d["name"].lower() == doc.name.lower():
            raise HTTPException(400, "Doctor already exists")
    new_doc = doc.dict()
    new_doc["id"] = len(doctors) + 1
    doctors.append(new_doc)
    return new_doc

@app.put("/doctors/{doctor_id}")
def update_doctor(doctor_id: int, fee: Optional[int] = None, is_available: Optional[bool] = None):
    doc = find_doctor(doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    if fee is not None:
        doc["fee"] = fee
    if is_available is not None:
        doc["is_available"] = is_available
    return doc

@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int):
    doc = find_doctor(doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    for a in appointments:
        if a["doctor_id"] == doctor_id and a["status"] in ["scheduled", "confirmed"]:
            raise HTTPException(400, "Doctor has active appointments")
    doctors.remove(doc)
    return {"message": "Doctor deleted"}

# -------------------- APPOINTMENTS --------------------

@app.post("/appointments", status_code=201)
def create_appointment(req: AppointmentRequest):
    global appt_counter
    doc = find_doctor(req.doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    if not doc["is_available"]:
        raise HTTPException(400, "Doctor not available")

    original_fee, final_fee = calculate_fee(doc["fee"], req.appointment_type, req.senior_citizen)

    appointment = {
        "appointment_id": appt_counter,
        "patient": req.patient_name,
        "doctor_name": doc["name"],
        "doctor_id": req.doctor_id,
        "date": req.date,
        "type": req.appointment_type,
        "original_fee": original_fee,
        "final_fee": final_fee,
        "status": "scheduled"
    }

    doc["is_available"] = False
    appointments.append(appointment)
    appt_counter += 1
    return appointment

@app.post("/appointments/{appointment_id}/confirm")
def confirm(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "confirmed"
            return a
    raise HTTPException(404, "Appointment not found")

@app.post("/appointments/{appointment_id}/cancel")
def cancel(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "cancelled"
            doc = find_doctor(a["doctor_id"])
            if doc:
                doc["is_available"] = True
            return a
    raise HTTPException(404, "Appointment not found")

@app.post("/appointments/{appointment_id}/complete")
def complete(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "completed"
            return a
    raise HTTPException(404, "Appointment not found")

@app.get("/appointments/active")
def active():
    return [a for a in appointments if a["status"] in ["scheduled", "confirmed"]]

@app.get("/appointments/by-doctor/{doctor_id}")
def by_doctor(doctor_id: int):
    return [a for a in appointments if a["doctor_id"] == doctor_id]

# -------------------- APPOINTMENT SEARCH/SORT/PAGE --------------------

@app.get("/appointments/search")
def search_appt(keyword: str):
    return [a for a in appointments if keyword.lower() in a["patient"].lower()]

@app.get("/appointments/sort")
def sort_appt(sort_by: str = "date"):
    return sorted(appointments, key=lambda x: x[sort_by])

@app.get("/appointments/page")
def page_appt(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    total_pages = math.ceil(len(appointments) / limit)
    return {"page": page, "total_pages": total_pages, "data": appointments[start:end]}

# -------------------- GET BY ID LAST --------------------

@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    doc = find_doctor(doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    return doc
