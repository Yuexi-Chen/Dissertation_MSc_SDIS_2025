def allocate_bed(patient, wards):
    patient_id = patient["id"]
    assigned_ward = None
    assigned_bed = None
    assigned_satellite_hospital = None

    for ward in wards:
        # Patient-Ward Matching
        condition_match = ward["target_condition"] == patient["condition"]
        gender_match = ward["gender_restriction"] == "Any" or ward["gender_restriction"] == patient["gender"]
        age_match = ward["age_restriction"][0] <= patient["age"] <= ward["age_restriction"][1]
        special_requirements_match = all(req in ward["special_requirements"] for req in patient["special_requirements"])

        if condition_match and gender_match and age_match and special_requirements_match:
            # Step 1: Regular Beds
            if ward["available_beds"]:
                assigned_ward = ward["ward_name"]
                assigned_bed = min(ward["available_beds"])
                ward["available_beds"].remove(assigned_bed)
                return {"patient_id": patient_id, "assigned_ward": assigned_ward, "assigned_bed": assigned_bed, "assigned_satellite_hospital": assigned_satellite_hospital}

            # Step 2: Overflow Beds
            if ward["overflow_capacity"] > 0:
                assigned_ward = ward["ward_name"]
                assigned_bed = f"Overflow-{ward['overflow_capacity']}"
                ward["overflow_capacity"] -= 1
                return {"patient_id": patient_id, "assigned_ward": assigned_ward, "assigned_bed": assigned_bed, "assigned_satellite_hospital": assigned_satellite_hospital}

            # Step 3: Satellite Hospitals
            if ward["satellite_hospitals"]:
                assigned_satellite_hospital = ward["satellite_hospitals"][0]
                assigned_ward = None
                assigned_bed = None
                return {"patient_id": patient_id, "assigned_ward": assigned_ward, "assigned_bed": assigned_bed, "assigned_satellite_hospital": assigned_satellite_hospital}

    # Step 4: No Assignment
    return {"patient_id": patient_id, "assigned_ward": assigned_ward, "assigned_bed": assigned_bed, "assigned_satellite_hospital": assigned_satellite_hospital}