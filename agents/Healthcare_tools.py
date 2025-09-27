from openai import OpenAI
from typing import Dict, Any, List
import datetime
from data.doctors_database import DOCTORS_DATABASE
from data.medicines_database import MEDICINES_DATABASE
from data.pharmacies_database import PHARMACIES_DATABASE

class HealthcareTools:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.doctors = DOCTORS_DATABASE
        self.medicines = MEDICINES_DATABASE
        self.pharmacies = PHARMACIES_DATABASE
    
    def schedule_appointment(self, preferred_date: str, preferred_time: str, doctor_specialization: str = None) -> Dict[str, Any]:
        """Schedule appointment with available doctor"""
        try:
            # Find available doctor
            available_doctors = [d for d in self.doctors if not doctor_specialization or d['specialization'].lower() == doctor_specialization.lower()]
            
            if not available_doctors:
                return {"error": f"No {doctor_specialization or 'doctors'} available"}
            
            doctor = available_doctors[0]  # Simple selection
            
            # Parse datetime
            scheduled_time = self._parse_datetime(preferred_date, preferred_time)
            if not scheduled_time:
                return {"error": "Invalid date/time format. Use YYYY-MM-DD and HH:MM"}
            
            return {
                "success": True,
                "appointment_id": len(self.doctors) + 1,  # Simple ID generation
                "doctor_name": doctor['name'],
                "specialization": doctor['specialization'],
                "fee": doctor['fee'],
                "scheduled_time": scheduled_time.isoformat(),
                "message": f"Appointment scheduled with {doctor['name']} ({doctor['specialization']}) on {scheduled_time.strftime('%A, %B %d at %I:%M %p')}"
            }
        except Exception as e:
            return {"error": f"Appointment scheduling failed: {str(e)}"}
    
    def search_medicines(self, medicine_name: str) -> Dict[str, Any]:
        """Search medicines in database"""
        try:
            found_medicines = [m for m in self.medicines if medicine_name.lower() in m['name'].lower()]
            
            if not found_medicines:
                return {"error": f"Medicine '{medicine_name}' not found"}
            
            # Get prices from pharmacies
            medicine_prices = []
            for pharmacy in self.pharmacies:
                price = len(medicine_name) * 10 + len(pharmacy['name'])  # Simple price calculation
                medicine_prices.append({
                    "pharmacy": pharmacy['name'],
                    "price": price,
                    "delivery_time": pharmacy['delivery_time'],
                    "contact": pharmacy['phone']
                })
            
            return {
                "success": True,
                "medicines": found_medicines,
                "prices": medicine_prices,
                "best_option": min(medicine_prices, key=lambda x: x['price'])
            }
        except Exception as e:
            return {"error": f"Medicine search failed: {str(e)}"}
    
    def order_medicine(self, medicine_name: str, pharmacy_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Place medicine order"""
        try:
            pharmacy = next((p for p in self.pharmacies if p['id'] == pharmacy_id), None)
            if not pharmacy:
                return {"error": "Pharmacy not found"}
            
            medicine = next((m for m in self.medicines if medicine_name.lower() in m['name'].lower()), None)
            if not medicine:
                return {"error": "Medicine not found"}
            
            price = len(medicine_name) * 10 * quantity
            
            return {
                "success": True,
                "order_id": len(self.pharmacies) + 1,
                "medicine": medicine['name'],
                "pharmacy": pharmacy['name'],
                "quantity": quantity,
                "total_amount": price,
                "delivery_time": pharmacy['delivery_time'],
                "contact": pharmacy['phone'],
                "message": f"Order placed for {quantity} {medicine['name']} with {pharmacy['name']}"
            }
        except Exception as e:
            return {"error": f"Order failed: {str(e)}"}
    
    def symptom_checker(self, symptoms: List[str], age: int) -> Dict[str, Any]:
        """Basic symptom analysis"""
        try:
            symptoms_text = ", ".join(symptoms).lower()
            
            # Simple symptom analysis
            if any(s in symptoms_text for s in ['fever', 'cough', 'cold']):
                analysis = "Possible viral infection or common cold"
                recommendation = "Rest, hydrate, take paracetamol if needed"
            elif any(s in symptoms_text for s in ['headache', 'migraine']):
                analysis = "Tension headache or migraine"
                recommendation = "Rest in quiet room, avoid bright lights"
            else:
                analysis = "General symptoms observed"
                recommendation = "Monitor symptoms and consult doctor if persistent"
            
            return {
                "success": True,
                "analysis": analysis,
                "recommendation": recommendation,
                "urgency": "Non-emergency",
                "advice": "Consult doctor if symptoms worsen"
            }
        except Exception as e:
            return {"error": f"Symptom analysis failed: {str(e)}"}
    
    def _parse_datetime(self, date_str: str, time_str: str) -> datetime.datetime:
        """Parse datetime from strings"""
        try:
            return datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except:
            try:
                return datetime.datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
            except:
                return datetime.datetime.now() + datetime.timedelta(days=1)