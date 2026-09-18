"""
Seeds the database with:
  * A demo admin, doctor, and patient account (so the app is usable immediately)
  * A starter medical knowledge base: ~20 common diseases, ~35 symptoms with
    disease links, and a handful of medications
  * Triggers an initial RAG reindex so chat/diagnosis work immediately

Run from the backend/ directory:
    python scripts/seed_data.py

IMPORTANT: the disease/symptom/medication content below is simplified,
general-public educational information intended to make the platform
demoable out of the box. Before any real-world deployment, this content
must be reviewed and expanded by qualified medical professionals through
the admin Knowledge Base Management panel.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401
from app.models.disease import Disease, DiseaseSymptom, Symptom
from app.models.emergency import Hospital, Pharmacy
from app.models.medication import Medication
from app.models.user import DoctorProfile, PatientProfile, User, UserRole
from app.services.rag.indexer import reindex_all

SYMPTOMS = [
    ("Fever", "Elevated body temperature above the normal range", "general"),
    ("Cough", "Reflex action to clear the airways", "respiratory"),
    ("Runny nose", "Excess drainage from the nasal passages", "respiratory"),
    ("Nasal congestion", "Blocked or stuffy nose", "respiratory"),
    ("Sore throat", None, "respiratory"),
    ("Throat pain", None, "respiratory"),
    ("Shortness of breath", "Difficulty breathing or feeling breathless", "respiratory"),
    ("Difficulty breathing", None, "respiratory"),
    ("Wheezing", "A whistling sound while breathing", "respiratory"),
    ("Chest pain", None, "cardiovascular"),
    ("Headache", None, "neurological"),
    ("Dizziness", None, "neurological"),
    ("Fatigue", "Persistent tiredness or low energy", "general"),
    ("Body pain", "Generalized muscle or body aches", "musculoskeletal"),
    ("Joint pain", None, "musculoskeletal"),
    ("Nausea", None, "gastrointestinal"),
    ("Vomiting", None, "gastrointestinal"),
    ("Diarrhea", None, "gastrointestinal"),
    ("Abdominal pain", None, "gastrointestinal"),
    ("Loss of appetite", None, "gastrointestinal"),
    ("Skin itching", None, "skin"),
    ("Skin rash", None, "skin"),
    ("Skin redness", None, "skin"),
    ("Dry skin", None, "skin"),
    ("Eye redness", None, "eye"),
    ("Eye itching", None, "eye"),
    ("Eye discharge", None, "eye"),
    ("Blurred vision", None, "eye"),
    ("Sensitivity to light", None, "neurological"),
    ("Sneezing", None, "respiratory"),
    ("Chills", None, "general"),
    ("Sweating", None, "general"),
    ("Weight loss", None, "general"),
    ("Insomnia", "Difficulty falling or staying asleep", "neurological"),
    ("Swollen lymph nodes", None, "general"),
]

# (name, severity, recommended_specialist, avg_recovery_days, description, symptoms[(name, importance)])
DISEASES = [
    (
        "Common Cold",
        "mild",
        "General Physician",
        7,
        "A mild viral infection of the nose and throat, usually harmless and resolving on its own.",
        "Stay hydrated, rest, and use a humidifier.",
        "Warm soups, herbal tea, citrus fruits",
        "Cold drinks, sugary snacks",
        "If symptoms persist beyond 10 days or fever exceeds 39°C.",
        [("Runny nose", 0.9), ("Nasal congestion", 0.85), ("Sneezing", 0.7), ("Sore throat", 0.6), ("Cough", 0.5), ("Fever", 0.3)],
    ),
    (
        "Influenza",
        "moderate",
        "General Physician",
        10,
        "A contagious respiratory illness caused by influenza viruses, generally more severe than a common cold.",
        "Rest, fluids, and over-the-counter fever reducers as needed.",
        "Broth-based soups, bananas, oatmeal",
        "Alcohol, caffeine, processed foods",
        "Difficulty breathing, chest pain, persistent high fever, or symptoms that improve then worsen.",
        [("Fever", 0.9), ("Body pain", 0.85), ("Fatigue", 0.8), ("Cough", 0.7), ("Chills", 0.65), ("Headache", 0.5), ("Sore throat", 0.4)],
    ),
    (
        "Migraine",
        "moderate",
        "Neurologist",
        2,
        "A neurological condition causing intense, throbbing headaches often with nausea and light sensitivity.",
        "Rest in a dark, quiet room; apply a cold compress.",
        "Magnesium-rich foods like spinach and almonds",
        "Aged cheese, processed meats, excess caffeine",
        "Sudden, severe 'worst headache of your life', vision loss, or neurological symptoms.",
        [("Headache", 0.95), ("Sensitivity to light", 0.7), ("Nausea", 0.6), ("Dizziness", 0.4), ("Blurred vision", 0.3)],
    ),
    (
        "Gastroenteritis",
        "moderate",
        "Gastroenterologist",
        5,
        "Inflammation of the stomach and intestines, commonly caused by viral or bacterial infection.",
        "Stay hydrated with oral rehydration solutions; eat bland foods (BRAT diet).",
        "Bananas, rice, applesauce, toast",
        "Dairy, fatty or spicy foods, alcohol",
        "Signs of severe dehydration, blood in stool, or high fever.",
        [("Diarrhea", 0.9), ("Vomiting", 0.8), ("Abdominal pain", 0.8), ("Nausea", 0.75), ("Fever", 0.4), ("Loss of appetite", 0.5)],
    ),
    (
        "Allergic Rhinitis",
        "mild",
        "Allergist / Immunologist",
        14,
        "An allergic response of the nasal passages to airborne allergens like pollen or dust.",
        "Avoid known allergens, use air purifiers, keep windows closed during high pollen seasons.",
        "Foods rich in vitamin C and quercetin (apples, onions)",
        "Foods you have identified as personal allergens",
        "Severe facial swelling or difficulty breathing (possible anaphylaxis — emergency).",
        [("Sneezing", 0.85), ("Runny nose", 0.8), ("Nasal congestion", 0.75), ("Eye itching", 0.6), ("Eye redness", 0.4)],
    ),
    (
        "Eczema (Atopic Dermatitis)",
        "mild",
        "Dermatologist",
        30,
        "A chronic skin condition causing dry, itchy, inflamed patches of skin.",
        "Moisturize regularly, use gentle fragrance-free soap, avoid known triggers.",
        "Omega-3 rich foods like salmon and flaxseed",
        "Foods you've identified as personal triggers, excess sugar",
        "Signs of skin infection (pus, increasing redness, fever).",
        [("Skin itching", 0.9), ("Skin redness", 0.7), ("Dry skin", 0.75), ("Skin rash", 0.6)],
    ),
    (
        "Conjunctivitis (Pink Eye)",
        "mild",
        "Ophthalmologist",
        7,
        "Inflammation of the membrane covering the eye, often due to infection or allergy.",
        "Use a clean, warm compress; avoid touching/rubbing the eyes; wash hands frequently.",
        "Foods rich in vitamin A like carrots and sweet potatoes",
        "—",
        "Significant pain, vision changes, or symptoms not improving after a few days.",
        [("Eye redness", 0.9), ("Eye discharge", 0.8), ("Eye itching", 0.7)],
    ),
    (
        "Strep Throat",
        "moderate",
        "General Physician",
        7,
        "A bacterial infection causing inflammation and pain in the throat.",
        "Rest, warm salt-water gargles, throat lozenges.",
        "Warm broths, smoothies, mashed soft foods",
        "Spicy, acidic, or crunchy foods that irritate the throat",
        "Difficulty swallowing/breathing, high fever, or a rash.",
        [("Throat pain", 0.9), ("Sore throat", 0.85), ("Fever", 0.7), ("Swollen lymph nodes", 0.6)],
    ),
    (
        "Bronchitis",
        "moderate",
        "Pulmonologist",
        14,
        "Inflammation of the bronchial tubes that carry air to the lungs, often following a cold.",
        "Rest, stay hydrated, use a humidifier, avoid smoke exposure.",
        "Warm fluids, ginger tea, honey",
        "Smoking/secondhand smoke, cold drinks",
        "Coughing up blood, high fever, or severe shortness of breath.",
        [("Cough", 0.9), ("Shortness of breath", 0.6), ("Wheezing", 0.6), ("Fatigue", 0.5), ("Chest pain", 0.4)],
    ),
    (
        "Asthma Exacerbation",
        "severe",
        "Pulmonologist",
        3,
        "A flare-up of asthma symptoms due to airway inflammation and narrowing.",
        "Use prescribed rescue inhaler, avoid known triggers, sit upright.",
        "Anti-inflammatory foods like leafy greens and berries",
        "Foods/additives known to trigger your symptoms",
        "Rescue inhaler not helping, lips/face turning blue, or extreme difficulty speaking — call emergency services.",
        [("Wheezing", 0.9), ("Shortness of breath", 0.9), ("Chest pain", 0.5), ("Difficulty breathing", 0.85)],
    ),
    (
        "Tension Headache",
        "mild",
        "General Physician",
        1,
        "The most common type of headache, often related to stress or muscle tension.",
        "Rest, gentle neck stretches, stay hydrated, manage stress.",
        "Magnesium-rich foods, water",
        "Excess caffeine, alcohol",
        "Sudden severe headache, headache with fever and stiff neck, or after a head injury.",
        [("Headache", 0.85), ("Fatigue", 0.3)],
    ),
    (
        "Iron-Deficiency Anemia",
        "moderate",
        "Hematologist",
        60,
        "A condition where the blood lacks enough healthy red blood cells due to low iron.",
        "Eat iron-rich foods, consider supplements as advised by a doctor.",
        "Red meat, spinach, lentils, fortified cereals",
        "Tea/coffee with meals (inhibits iron absorption)",
        "Chest pain, rapid heartbeat, or severe weakness.",
        [("Fatigue", 0.85), ("Dizziness", 0.6), ("Headache", 0.3)],
    ),
    (
        "Urinary Tract Infection",
        "moderate",
        "Urologist",
        7,
        "A bacterial infection affecting any part of the urinary system.",
        "Drink plenty of water, urinate frequently, avoid holding urine.",
        "Cranberries, water, vitamin C rich foods",
        "Caffeine, alcohol, spicy foods",
        "Fever with chills, back/flank pain (possible kidney involvement).",
        [("Abdominal pain", 0.5), ("Fever", 0.4)],
    ),
    (
        "Acne Vulgaris",
        "mild",
        "Dermatologist",
        45,
        "A common skin condition causing pimples, often due to clogged hair follicles.",
        "Gentle cleansing twice daily, avoid picking at lesions, non-comedogenic products.",
        "Low-glycemic foods, water",
        "High-sugar and high-dairy foods (may worsen for some individuals)",
        "Painful cystic lesions or scarring — see a dermatologist for prescription treatment.",
        [("Skin rash", 0.6), ("Skin redness", 0.5)],
    ),
    (
        "Tonsillitis",
        "moderate",
        "ENT Specialist",
        7,
        "Inflammation of the tonsils, usually due to viral or bacterial infection.",
        "Warm salt-water gargles, rest, throat lozenges.",
        "Soft, cool foods like yogurt and smoothies",
        "Hard, crunchy, or spicy foods",
        "Severe difficulty breathing/swallowing or high fever.",
        [("Throat pain", 0.85), ("Fever", 0.6), ("Swollen lymph nodes", 0.5), ("Sore throat", 0.8)],
    ),
    (
        "Insomnia",
        "mild",
        "General Physician",
        21,
        "Persistent difficulty falling or staying asleep, affecting daytime functioning.",
        "Maintain a consistent sleep schedule, limit screens before bed, relaxing bedtime routine.",
        "Foods with tryptophan/magnesium like turkey and almonds",
        "Caffeine and heavy meals close to bedtime",
        "Insomnia lasting weeks alongside mood changes — consider professional support.",
        [("Insomnia", 0.9), ("Fatigue", 0.5)],
    ),
    (
        "Generalized Anxiety",
        "moderate",
        "Psychiatrist",
        None,
        "A condition involving persistent, excessive worry that interferes with daily life.",
        "Practice relaxation techniques, regular exercise, consider talking to a therapist.",
        "Omega-3 rich foods, complex carbohydrates",
        "Excess caffeine and alcohol",
        "Thoughts of self-harm — seek immediate professional help.",
        [("Insomnia", 0.5), ("Fatigue", 0.5), ("Headache", 0.3), ("Dizziness", 0.3)],
    ),
    (
        "Food Poisoning",
        "moderate",
        "Gastroenterologist",
        3,
        "Illness caused by consuming contaminated food, leading to gastrointestinal symptoms.",
        "Rest, rehydrate with electrolyte solutions, gradually reintroduce bland foods.",
        "Bananas, rice, toast, clear broths",
        "Dairy, fatty, spicy, or sugary foods",
        "Bloody stool, signs of severe dehydration, or fever above 39°C.",
        [("Vomiting", 0.85), ("Diarrhea", 0.85), ("Abdominal pain", 0.75), ("Nausea", 0.7), ("Fever", 0.4)],
    ),
    (
        "Hypertension (High Blood Pressure)",
        "moderate",
        "Cardiologist",
        None,
        "A chronic condition where blood pressure against artery walls is persistently too high.",
        "Reduce sodium intake, exercise regularly, manage stress, monitor blood pressure.",
        "Leafy greens, berries, oats, low-sodium foods",
        "High-sodium processed foods, excess alcohol",
        "Severe headache, chest pain, or blood pressure reading above 180/120.",
        [("Headache", 0.4), ("Dizziness", 0.4), ("Chest pain", 0.3)],
    ),
    (
        "Pneumonia",
        "severe",
        "Pulmonologist",
        21,
        "An infection that inflames the air sacs in one or both lungs, which may fill with fluid.",
        "Complete prescribed antibiotics if bacterial, rest, stay hydrated.",
        "Protein-rich foods, warm fluids",
        "Smoking, alcohol",
        "Bluish lips/face, severe difficulty breathing, or confusion — seek emergency care immediately.",
        [("Fever", 0.7), ("Cough", 0.7), ("Shortness of breath", 0.75), ("Chest pain", 0.6), ("Fatigue", 0.5), ("Difficulty breathing", 0.7)],
    ),
]

MEDICATIONS = [
    (
        "Paracetamol (Acetaminophen)",
        "Acetaminophen",
        "Analgesic / Antipyretic",
        "General pain relief and fever reduction",
        "Severe liver disease",
        "Nausea (rare at normal doses), liver damage at high doses",
        "Avoid combining with other acetaminophen-containing products",
        "Generally considered safe at standard doses",
        "Considered safe in pregnancy at recommended doses — confirm with your doctor",
        "Store at room temperature, away from moisture",
        False,
        "Common Cold,Influenza,Tension Headache,Strep Throat,Tonsillitis",
    ),
    (
        "Ibuprofen",
        "Ibuprofen",
        "NSAID (Anti-inflammatory)",
        "Pain relief, fever reduction, inflammation reduction",
        "Active stomach ulcers, severe kidney disease, late pregnancy",
        "Stomach upset, increased bleeding risk, kidney strain with prolonged use",
        "Avoid combining with other NSAIDs or blood thinners without medical advice",
        "Not typically recommended under 6 months of age",
        "Avoid in third trimester unless directed by a doctor",
        "Store at room temperature",
        False,
        "Influenza,Migraine,Body Pain,Tension Headache",
    ),
    (
        "Loratadine",
        "Loratadine",
        "Antihistamine",
        "Allergy symptom relief (sneezing, itching, runny nose)",
        "Known hypersensitivity to loratadine",
        "Mild drowsiness (less than older antihistamines), dry mouth",
        "Limited significant interactions; consult a pharmacist if on multiple medications",
        "Pediatric dosing forms available — follow age-specific guidance",
        "Consult your doctor regarding use during pregnancy",
        "Store at room temperature",
        False,
        "Allergic Rhinitis,Conjunctivitis (Pink Eye)",
    ),
    (
        "Oral Rehydration Salts (ORS)",
        "Sodium chloride, potassium chloride, glucose",
        "Electrolyte replacement",
        "Rehydration after fluid loss from vomiting/diarrhea",
        "None significant at standard use",
        "Rare; nausea if concentration is too high",
        "None significant",
        "Safe for all ages including infants when properly mixed",
        "Safe during pregnancy",
        "Mix fresh with clean water; discard unused mixed solution after 24 hours",
        False,
        "Gastroenteritis,Food Poisoning",
    ),
    (
        "Hydrocortisone Cream 1%",
        "Hydrocortisone",
        "Topical corticosteroid",
        "Short-term relief of skin itching and inflammation",
        "Active untreated skin infections at the application site",
        "Skin thinning with prolonged use, local irritation",
        "Avoid combining with other strong topical steroids",
        "Use a lower concentration and shorter duration in children — consult a doctor",
        "Generally considered low-risk topically — confirm with your doctor",
        "Store at room temperature",
        False,
        "Eczema (Atopic Dermatitis),Acne Vulgaris",
    ),
    (
        "Amoxicillin",
        "Amoxicillin",
        "Antibiotic (Penicillin class)",
        "Bacterial infections such as strep throat, certain UTIs and pneumonia",
        "Known penicillin allergy",
        "Diarrhea, rash, rarely allergic reaction",
        "May reduce effectiveness of some hormonal contraceptives",
        "Pediatric dosing available based on weight",
        "Generally considered safe in pregnancy — confirm with your doctor",
        "Store as directed; some formulations require refrigeration",
        True,
        "Strep Throat,Urinary Tract Infection,Tonsillitis,Pneumonia",
    ),
]


# (name, address, lat, lon, phone, specialties, has_emergency_room)
HOSPITALS = [
    (
        "Republican Specialized Scientific-Practical Medical Center of Surgery",
        "Farkhadskaya St 10, Tashkent",
        41.2856,
        69.2034,
        "+998 71 277 71 71",
        "General Surgery, Trauma, Emergency Medicine",
        True,
    ),
    (
        "Tashkent City Clinical Hospital",
        "Navoi St 1, Tashkent",
        41.3111,
        69.2797,
        "+998 71 233 45 67",
        "Internal Medicine, Cardiology, Emergency Medicine",
        True,
    ),
    (
        "Republican Perinatal Center",
        "Taras Shevchenko St 1, Tashkent",
        41.3194,
        69.2787,
        "+998 71 150 78 88",
        "Obstetrics, Gynecology, Neonatology",
        True,
    ),
    (
        "Tashkent Medical Academy Clinic",
        "Farobiy St 2, Tashkent",
        41.3275,
        69.2540,
        "+998 71 268 56 27",
        "General Medicine, Internal Medicine, Pediatrics",
        True,
    ),
    (
        "National Children's Medical Center",
        "Chimboy St 1, Tashkent",
        41.3019,
        69.2401,
        "+998 71 277 87 78",
        "Pediatrics, Pediatric Surgery",
        True,
    ),
    (
        "Republican Specialized Center of Ophthalmology",
        "Kichik Halqa Yoli, Tashkent",
        41.3354,
        69.2884,
        "+998 71 268 51 12",
        "Ophthalmology",
        False,
    ),
]

# (name, address, lat, lon, phone, is_24h)
PHARMACIES = [
    ("Apteka 36.6 — Amir Temur", "Amir Temur Ave 45, Tashkent", 41.3111, 69.2797, "+998 71 200 36 36", True),
    ("Oson Apteka — Chilanzar", "Bunyodkor Ave 12, Tashkent", 41.2856, 69.2034, "+998 71 200 11 22", True),
    ("Doris Apteka — Yunusabad", "Amir Temur Shox Ko'chasi 90, Tashkent", 41.3489, 69.2887, "+998 71 200 33 44", False),
    ("Salomatlik Apteka — Mirzo Ulugbek", "Universitet Ko'chasi 4, Tashkent", 41.3275, 69.2540, "+998 71 200 55 66", True),
]


def _build_session_factory():
    database_url = settings.DATABASE_URL
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

    try:
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=280 if not database_url.startswith("sqlite") else -1,
        )
        with engine.connect():
            pass
    except OperationalError:
        if database_url.startswith("sqlite"):
            raise

        fallback_url = "sqlite:///./medvision_dev.db"
        print(f"Warning: unable to connect to {database_url!r}; falling back to {fallback_url!r} for local seeding.")
        database_url = fallback_url
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            pool_recycle=-1,
        )

    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run() -> None:
    SessionLocal = _build_session_factory()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "admin@medvision.ai").first():
            print("Database already seeded — skipping. Delete data manually if you want to reseed.")
            return

        print("Creating demo accounts...")
        admin = User(
            email="admin@medvision.ai",
            hashed_password=hash_password("Admin@12345"),
            full_name="Platform Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        doctor_user = User(
            email="doctor@medvision.ai",
            hashed_password=hash_password("Doctor@12345"),
            full_name="Dr. Aziza Karimova",
            role=UserRole.DOCTOR,
            is_active=True,
            is_email_verified=True,
        )
        patient_user = User(
            email="patient@medvision.ai",
            hashed_password=hash_password("Patient@12345"),
            full_name="Demo Patient",
            role=UserRole.PATIENT,
            is_active=True,
            is_email_verified=True,
        )
        db.add_all([admin, doctor_user, patient_user])
        db.flush()

        db.add(DoctorProfile(user_id=doctor_user.id, specialty="General Medicine", is_verified=True, years_experience=8))
        db.add(PatientProfile(user_id=patient_user.id))

        print("Seeding symptoms...")
        symptom_objs: dict[str, Symptom] = {}
        for name, description, body_system in SYMPTOMS:
            s = Symptom(name=name, description=description, body_system=body_system)
            db.add(s)
            symptom_objs[name] = s
        db.flush()

        print("Seeding diseases + symptom links...")
        for (
            name,
            severity,
            specialist,
            recovery_days,
            description,
            lifestyle_advice,
            foods_to_eat,
            foods_to_avoid,
            emergency_signs,
            symptom_links,
        ) in DISEASES:
            disease = Disease(
                name=name,
                severity=severity,
                recommended_specialist=specialist,
                avg_recovery_days=recovery_days,
                description=description,
                lifestyle_advice=lifestyle_advice,
                foods_to_eat=foods_to_eat,
                foods_to_avoid=foods_to_avoid,
                emergency_warning_signs=emergency_signs,
                tags=name,
            )
            db.add(disease)
            db.flush()
            for symptom_name, importance in symptom_links:
                db.add(
                    DiseaseSymptom(
                        disease_id=disease.id,
                        symptom_id=symptom_objs[symptom_name].id,
                        importance_score=importance,
                    )
                )

        print("Seeding medications...")
        for (
            name,
            active_ingredient,
            category,
            indications,
            contraindications,
            side_effects,
            interactions,
            age_restrictions,
            pregnancy,
            storage,
            rx_required,
            linked_tags,
        ) in MEDICATIONS:
            db.add(
                Medication(
                    name=name,
                    active_ingredient=active_ingredient,
                    drug_category=category,
                    general_indications=indications,
                    contraindications=contraindications,
                    possible_side_effects=side_effects,
                    drug_interactions=interactions,
                    age_restrictions=age_restrictions,
                    pregnancy_considerations=pregnancy,
                    storage_information=storage,
                    prescription_required=rx_required,
                    linked_disease_tags=linked_tags,
                )
            )

        db.commit()

        print("Seeding hospitals and pharmacies (Tashkent)...")
        for name, address, lat, lon, phone, specialties, has_er in HOSPITALS:
            db.add(
                Hospital(
                    name=name, address=address, latitude=lat, longitude=lon, phone=phone,
                    specialties=specialties, has_emergency_room=has_er,
                )
            )
        for name, address, lat, lon, phone, is_24h in PHARMACIES:
            db.add(Pharmacy(name=name, address=address, latitude=lat, longitude=lon, phone=phone, is_24h=is_24h))
        db.commit()

        print("Building the RAG index from the seeded knowledge base...")
        count = reindex_all(db)
        print(f"Indexed {count} knowledge chunks.")

        print("\nSeed complete. Demo accounts:")
        print("  Admin:   admin@medvision.ai   / Admin@12345")
        print("  Doctor:  doctor@medvision.ai  / Doctor@12345")
        print("  Patient: patient@medvision.ai / Patient@12345")
    finally:
        db.close()


if __name__ == "__main__":
    run()
