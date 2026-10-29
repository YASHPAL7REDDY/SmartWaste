import sys
sys.path.insert(0, '.')
from app.database.session import SessionLocal
from app.models.prediction import AreaPrediction, OverflowRiskPrediction
from app.models.waste import AreaCollection
from app.models.user import Collector
from datetime import date, datetime
import json

db = SessionLocal()
try:
    today = date.today()
    now = datetime.now()
    
    # Get all overflow risks for today
    risks = db.query(OverflowRiskPrediction).filter(
        OverflowRiskPrediction.prediction_date == today
    ).all()
    
    print(f'Found {len(risks)} overflow risks for today')
    
    # Get collectors
    collectors = db.query(Collector).filter(Collector.is_active == True).all()
    print(f'Found {len(collectors)} active collectors')
    
    # Deduplicate risks by area (keep the one with highest risk level)
    risk_by_area = {}
    risk_priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    
    for risk in risks:
        area = risk.area
        risk_level = (risk.risk_level or "low").lower()
        current_priority = risk_priority_order.get(risk_level, 1)
        
        if area not in risk_by_area or current_priority > risk_by_area[area][1]:
            risk_by_area[area] = (risk, current_priority)
    
    print(f'Deduplicated to {len(risk_by_area)} unique areas')
    
    # Get collectors
    collectors = db.query(Collector).filter(Collector.is_active == True).all()
    print(f'Found {len(collectors)} active collectors')
    
    # Create AreaCollection records for areas with overflow risks
    created_count = 0
    for area, (risk, _) in risk_by_area.items():
        # Check if collection already exists for this area and date
        existing = db.query(AreaCollection).filter(
            AreaCollection.area == area,
            AreaCollection.collection_date == date.today()
        ).first()
        
        if existing:
            print(f'Collection already exists for {area}')
            continue
        
        # Find a collector assigned to this area
        assigned_collector = None
        for collector in collectors:
            if collector.assigned_areas and area in collector.assigned_areas:
                assigned_collector = collector
                break
        
        # If no collector assigned to this area, use the first collector
        if not assigned_collector and collectors:
            assigned_collector = collectors[0]
        
        if not assigned_collector:
            print(f'No collector available for {area}')
            continue
        
        # Determine priority based on risk level
        risk_priority = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
        priority = risk_priority.get(risk.risk_level.lower(), "NORMAL")
        
        # Create waste breakdown from risk prediction
        waste_breakdown = {
            "wet": float(risk.wet_predicted_kg or 0),
            "dry": float(risk.dry_predicted_kg or 0),
            "plastic": float(risk.plastic_predicted_kg or 0),
            "glass": float(risk.glass_predicted_kg or 0),
            "metal": float(risk.metal_predicted_kg or 0),
            "medical": float(risk.medical_predicted_kg or 0)
        }
        
        # Determine priority based on risk level
        risk_priority_map = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
        priority = risk_priority_map.get(risk.risk_level.lower(), "NORMAL")
        
        # Create waste breakdown from risk prediction
        waste_breakdown = {
            "wet": float(risk.wet_predicted_kg or 0),
            "dry": float(risk.dry_predicted_kg or 0),
            "plastic": float(risk.plastic_predicted_kg or 0),
            "glass": float(risk.glass_predicted_kg or 0),
            "metal": float(risk.metal_predicted_kg or 0),
            "medical": float(risk.medical_predicted_kg or 0)
        }
        
        # Create AreaCollection
        now = datetime.now()
        collection = AreaCollection(
            id=f"col_{risk.area}_{date.today().isoformat()}",
            area=risk.area,
            collector_id=assigned_collector.id if assigned_collector else None,
            collection_date=date.today(),
            status="assigned",
            predicted_waste_kg=risk.predicted_total_waste_kg,
            collected_waste_kg=0.0,
            started_at=None,
            completed_at=None,
            waste_breakdown_predicted=json.dumps(waste_breakdown),
            facility_assignments=None,
            route_sequence=None,
            planned_load_kg=risk.predicted_total_waste_kg,
            waste_breakdown_collected=None,
            actual_sequence=None,
            actual_collection_time=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(collection)
        print(f'Created collection for {risk.area} (Risk: {risk.risk_level}, Priority: {priority})')
    
    db.commit()
    print('Done creating collections for today')
finally:
    db.close()