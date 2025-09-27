from agents import Agent, Runner, tool
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import datetime

from database.crud import CRUDManager
from context.global_context import GlobalContext
from data.doctors_database import DOCTORS_DATABASE
from data.medicines_database import MEDICINES_DATABASE
from data.pharmacies_database import PHARMACIES_DATABASE

# Tool Input Models
class ScheduleAppointmentInput(BaseModel):
    preferred_date: str
    preferred_time: str
    doctor_specialization: Optional[str] = None

class SearchMedicineInput(BaseModel):
    medicine_name: str

class OrderMedicineInput(BaseModel):
    medicine_name: str
    pharmacy_id: int
    quantity: int = 1

class SymptomCheckInput(BaseModel):
    symptoms: List[str]
    age: int

class HealthcareTools:
    def __init__(self, db_manager: CRUDManager, context: GlobalContext):
        self.db = db_manager
        self.context = context
        self.doctors = DOCTORS_DATABASE
        self.medicines = MEDICINES_DATABASE
        self.pharmacies = PHARMACIES_DATABASE

    @tool
    def schedule_appointment(self, input: ScheduleAppointmentInput) -> Dict[str, Any]:
        """Schedule a medical appointment with an available doctor."""
        try:
            # Find available doctor based on specialization
            available_doctors = [
                d for d in self.doctors 
                if not input.doctor_specialization or d['specialization'].lower() == input.doctor_specialization.lower()
            ]
            
            if not available_doctors:
                return {"error": f"No {input.doctor_specialization or 'doctors'} available at the moment"}
            
            doctor = available_doctors[0]
            
            # Parse datetime
            scheduled_time = self._parse_datetime(input.preferred_date, input.preferred_time)
            if not scheduled_time:
                return {"error": "Please provide date and time in format: YYYY-MM-DD and HH:MM"}
            
            # Create appointment in database
            appointment_data = {
                "user_id": self.context.user.id,
                "doctor_id": doctor['id'],
                "doctor_name": doctor['name'],
                "appointment_type": doctor['specialization'],
                "scheduled_time": scheduled_time,
                "status": "scheduled"
            }
            
            appointment = self.db.create_appointment(appointment_data)
            
            return {
                "success": True,
                "appointment_id": appointment.id,
                "doctor_name": doctor['name'],
                "specialization": doctor['specialization'],
                "experience": doctor['experience'],
                "fee": f"Rs. {doctor['fee']}",
                "scheduled_time": scheduled_time.strftime('%A, %B %d, %Y at %I:%M %p'),
                "message": f"Appointment successfully scheduled with {doctor['name']}"
            }
            
        except Exception as e:
            return {"error": f"Failed to schedule appointment: {str(e)}"}

    @tool
    def search_medicines(self, input: SearchMedicineInput) -> Dict[str, Any]:
        """Search for medicines across multiple pharmacies with price comparison."""
        try:
            found_medicines = [
                m for m in self.medicines 
                if input.medicine_name.lower() in m['name'].lower()
            ]
            
            if not found_medicines:
                return {"error": f"Medicine '{input.medicine_name}' not found in our database"}
            
            medicine = found_medicines[0]
            
            # Get prices from all pharmacies
            pharmacy_prices = []
            for pharmacy in self.pharmacies:
                price = self._calculate_medicine_price(medicine['name'], pharmacy['id'])
                pharmacy_prices.append({
                    "pharmacy_id": pharmacy['id'],
                    "pharmacy_name": pharmacy['name'],
                    "address": pharmacy['address'],
                    "price": price,
                    "delivery_time": pharmacy['delivery_time'],
                    "contact": pharmacy['phone'],
                    "rating": pharmacy['rating']
                })
            
            # Find best option (lowest price)
            best_option = min(pharmacy_prices, key=lambda x: x['price'])
            
            return {
                "success": True,
                "medicine": {
                    "name": medicine['name'],
                    "generic_name": medicine['generic_name'],
                    "type": medicine['type'],
                    "strength": medicine['strength'],
                    "common_uses": medicine['uses']
                },
                "available_pharmacies": pharmacy_prices,
                "best_option": best_option,
                "total_options": len(pharmacy_prices)
            }
            
        except Exception as e:
            return {"error": f"Medicine search failed: {str(e)}"}

    @tool
    def order_medicine(self, input: OrderMedicineInput) -> Dict[str, Any]:
        """Place an order for medicine from a specific pharmacy."""
        try:
            # Validate pharmacy
            pharmacy = next((p for p in self.pharmacies if p['id'] == input.pharmacy_id), None)
            if not pharmacy:
                return {"error": "Invalid pharmacy selection"}
            
            # Validate medicine
            medicine = next((m for m in self.medicines if input.medicine_name.lower() in m['name'].lower()), None)
            if not medicine:
                return {"error": f"Medicine '{input.medicine_name}' not available"}
            
            # Calculate price
            price = self._calculate_medicine_price(medicine['name'], pharmacy['id'])
            total_amount = price * input.quantity
            
            # Create order in database
            order_data = {
                "user_id": self.context.user.id,
                "pharmacy_id": pharmacy['id'],
                "pharmacy_name": pharmacy['name'],
                "medicines": [{
                    "name": medicine['name'],
                    "quantity": input.quantity,
                    "unit_price": price
                }],
                "total_amount": total_amount,
                "status": "confirmed",
                "delivery_address": self.context.user.address or "Will be confirmed by pharmacy"
            }
            
            order = self.db.create_medicine_order(order_data)
            
            return {
                "success": True,
                "order_id": order.id,
                "medicine": medicine['name'],
                "pharmacy": pharmacy['name'],
                "quantity": input.quantity,
                "unit_price": price,
                "total_amount": total_amount,
                "delivery_time": pharmacy['delivery_time'],
                "pharmacy_contact": pharmacy['phone'],
                "message": f"Order confirmed! {pharmacy['name']} will contact you within {pharmacy['delivery_time']}"
            }
            
        except Exception as e:
            return {"error": f"Order placement failed: {str(e)}"}

    @tool
    def symptom_checker(self, input: SymptomCheckInput) -> Dict[str, Any]:
        """Analyze symptoms and provide preliminary health guidance."""
        try:
            symptoms_text = ", ".join(input.symptoms).lower()
            
            # Basic symptom analysis logic
            if any(symptom in symptoms_text for symptom in ['fever', 'cough', 'cold', 'sore throat']):
                analysis = "Possible viral infection or common cold"
                recommendation = "Rest, stay hydrated, take paracetamol for fever"
                urgency = "Low"
            elif any(symptom in symptoms_text for symptom in ['chest pain', 'breathing difficulty', 'severe headache']):
                analysis = "Potential serious condition - requires immediate attention"
                recommendation = "Seek emergency medical care immediately"
                urgency = "High"
            elif any(symptom in symptoms_text for symptom in ['headache', 'migraine', 'dizziness']):
                analysis = "Possible tension headache or migraine"
                recommendation = "Rest in quiet environment, avoid bright lights"
                urgency = "Medium"
            else:
                analysis = "General symptoms observed"
                recommendation = "Monitor symptoms and consult healthcare provider"
                urgency = "Low"
            
            return {
                "success": True,
                "age": input.age,
                "symptoms_analyzed": input.symptoms,
                "preliminary_analysis": analysis,
                "recommendation": recommendation,
                "urgency_level": urgency,
                "next_steps": "Consult a healthcare professional for accurate diagnosis",
                "disclaimer": "This is AI-based guidance only, not medical diagnosis"
            }
            
        except Exception as e:
            return {"error": f"Symptom analysis failed: {str(e)}"}

    @tool
    def find_doctors(self, specialization: str = None) -> Dict[str, Any]:
        """Find doctors by specialization or list all available doctors."""
        try:
            if specialization:
                filtered_doctors = [d for d in self.doctors if specialization.lower() in d['specialization'].lower()]
                if not filtered_doctors:
                    return {"error": f"No {specialization} specialists available"}
                doctors_list = filtered_doctors
            else:
                doctors_list = self.doctors[:10]  # Limit to first 10
            
            return {
                "success": True,
                "doctors": doctors_list,
                "count": len(doctors_list),
                "message": f"Found {len(doctors_list)} doctors" + (f" in {specialization}" if specialization else "")
            }
            
        except Exception as e:
            return {"error": f"Doctor search failed: {str(e)}"}

    def _parse_datetime(self, date_str: str, time_str: str) -> Optional[datetime.datetime]:
        """Parse datetime from strings with multiple format support."""
        try:
            # Try different date formats
            for date_fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                for time_fmt in ['%H:%M', '%I:%M%p', '%I:%M %p']:
                    try:
                        return datetime.datetime.strptime(f"{date_str} {time_str}", f"{date_fmt} {time_fmt}")
                    except ValueError:
                        continue
            return None
        except Exception:
            return None

    def _calculate_medicine_price(self, medicine_name: str, pharmacy_id: int) -> int:
        """Calculate medicine price based on name and pharmacy."""
        base_price = len(medicine_name) * 20
        pharmacy_multiplier = {1: 1.0, 2: 1.1, 3: 0.9, 4: 1.2, 5: 1.0}
        return int(base_price * pharmacy_multiplier.get(pharmacy_id, 1.0))
