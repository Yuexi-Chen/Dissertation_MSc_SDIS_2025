def allocate_bed(patient, wards):
    patient_id = patient["id"]
    assigned_ward = None
    assigned_bed = None
    assigned_satellite_hospital = None

    for ward in wards:
        # Ward Matching
        if ward["target_condition"] == patient["condition"]:
            gender_restriction = ward["gender_restriction"]
            if (gender_restriction == "No Restriction" or gender_restriction == "No Gender Restriction" or
                (gender_restriction == "Male Only" and patient["gender"] == "Male") or
                (gender_restriction == "Female Only" and patient["gender"] == "Female")):
                age_restriction = ward["age_restriction"]
                if age_restriction[0] <= patient["age"] <= age_restriction[1]:
                    special_requirements = ward["special_requirements"]
                    patient_requirements = patient["special_requirements"]
                    if all(req in special_requirements for req in patient_requirements):
                        # Bed Allocation
                        if ward["available_beds"]:
                            assigned_bed = min(ward["available_beds"])
                            ward["available_beds"].remove(assigned_bed)
                            assigned_ward = ward["ward_name"]
                            break
                        elif ward["overflow_capacity"] > 0:
                            assigned_ward = ward["ward_name"]
                            assigned_bed = f"Overflow-{ward['overflow_capacity']}"
                            ward["overflow_capacity"] -= 1
                            break
                        elif ward["satellite_hospitals"]:
                            assigned_satellite_hospital = ward["satellite_hospitals"][0]
                            assigned_ward = None
                            assigned_bed = None
                            break

    return {
        "patient_id": patient_id,
        "assigned_ward": assigned_ward,
        "assigned_bed": assigned_bed,
        "assigned_satellite_hospital": assigned_satellite_hospital
    }

if __name__ == '__main__':
    import json
    import sys

    input_data = json.loads(sys.stdin.read())
    patient = input_data["patient"]
    wards = input_data["wards"]

    result = allocate_bed(patient, wards)
    print(json.dumps(result))