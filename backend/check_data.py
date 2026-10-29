import sys
sys.path.insert(0, '.')
from app.database.session import SessionLocal
from app.models.waste import AreaCollection, WasteSubmission, WasteItem
from app.models.prediction import AreaPrediction, OverflowRiskPrediction
from app.models.facility import WasteFacility, WasteGenerationZone
from datetime import date

db = SessionLocal()
try:
    # Check AreaCollections for today
    today = date.today()
    collections = db.query(AreaCollection).filter(AreaCollection.collection_date == today).all()
    print(f'AreaCollections for today ({today}): {len(collections)}')
    for c in collections:
        print(f'  ID: {c.id}, Area: {c.area}, Collector: {c.collector_id}, Status: {c.status}, Predicted: {c.predicted_waste_kg}, Seq: {c.route_sequence}')
    
    # Check all AreaCollections
    all_collections = db.query(AreaCollection).all()
    print(f'\nAll AreaCollections: {len(all_collections)}')
    for c in all_collections:
        print(f'  ID: {c.id}, Area: {c.area}, Date: {c.collection_date}, Collector: {c.collector_id}, Status: {c.status}')
    
    # Check WasteSubmissions
    submissions = db.query(WasteSubmission).all()
    print(f'\nWasteSubmissions: {len(submissions)}')
    for s in submissions[:5]:
        print(f'  ID: {s.id}, User: {s.user_id}, Date: {s.submission_date}, Area: {s.area_snapshot}, Total: {s.total_waste_kg}')
    
    # Check AreaPredictions
    area_preds = db.query(AreaPrediction).all()
    print(f'\nAreaPredictions: {len(area_preds)}')
    for p in area_preds[:5]:
        print(f'  ID: {p.id}, Area: {p.area}, Date: {p.prediction_date}, Total: {p.predicted_waste_kg}, Horizon: {p.horizon}')
    
    # Check OverflowRiskPredictions
    overflow = db.query(OverflowRiskPrediction).all()
    print(f'\nOverflowRiskPredictions: {len(overflow)}')
    for o in overflow[:5]:
        print(f'  ID: {o.id}, Area: {o.area}, Date: {o.prediction_date}, Risk: {o.risk_level}, Total: {o.predicted_total_waste_kg}')
    
    # Check Facilities
    facilities = db.query(WasteFacility).all()
    print(f'\nFacilities: {len(facilities)}')
    for f in facilities[:5]:
        print(f'  ID: {f.id}, Name: {f.facility_name}, Type: {f.facility_type}, Area: {f.area_name}, Categories: {f.waste_categories}')
    
    # Check WasteGenerationZones
    zones = db.query(WasteGenerationZone).all()
    print(f'\nWasteGenerationZones: {len(zones)}')
    for z in zones[:5]:
        print(f'  ID: {z.id}, Area: {z.area_name}, Total: {z.total_waste_kg_per_day}')
finally:
    db.close()