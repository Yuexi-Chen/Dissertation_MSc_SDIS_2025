def allocate_bed(patient, wards):
    patient_id = patient["id"]
    patient_gender = patient["gender"]
    patient_age = patient["age"]
    patient_condition = patient["condition"]
    patient_requirements = patient.get("special_requirements", [])

    for ward in wards:
        ward_name = ward["ward_name"]
        gender_restriction = ward["gender_restriction"]
        age_restriction = ward["age_restriction"]
        target_condition = ward["target_condition"]
        ward_requirements = ward.get("special_requirements", [])
        available_beds = ward.get("available_beds", [])
        overflow_capacity = ward.get("overflow_capacity", 0)
        satellite_hospitals = ward.get("satellite_hospitals", [])

        if (target_condition == patient_condition and
            (gender_restriction == "No Restriction" or 
             gender_restriction == "No Gender Restriction" or 
             gender_restriction == f"{patient_gender} Only") and
            age_restriction[0] <= patient_age <= age_restriction[1] and
            all(req in ward_requirements for req in patient_requirements)):
            
            if available_beds:
                assigned_bed = min(available_beds)
                return {
                    "patient_id": patient_id,
                    "assigned_ward": ward_name,
                    "assigned_bed": assigned_bed,
                    "assigned_satellite_hospital": None
                }

            if overflow_capacity > 0:
                assigned_bed = f"Overflow-1"
                return {
                    "patient_id": patient_id,
                    "assigned_ward": ward_name,
                    "assigned_bed": assigned_bed,
                    "assigned_satellite_hospital": None
                }

            if satellite_hospitals:
                assigned_hospital = satellite_hospitals[0]
                return {
                    "patient_id": patient_id,
                    "assigned_ward": None,
                    "assigned_bed": None,
                    "assigned_satellite_hospital": assigned_hospital
                }

    return {
        "patient_id": patient_id,
        "assigned_ward": None,
        "assigned_bed": None,
        "assigned_satellite_hospital": None
    }

def main():
    import sys, json
    input_data = json.load(sys.stdin)
    patient = input_data["patient"]
    wards = input_data["wards"]
    result = allocate_bed(patient, wards)
    print(json.dumps(result))

if __name__ == "__main__":
    main()