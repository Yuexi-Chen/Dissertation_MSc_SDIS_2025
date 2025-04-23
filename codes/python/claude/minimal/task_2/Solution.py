import json
import sys

def reallocate_bed(patient, hospitals):
    result = {
        "patient_id": patient["id"],
        "assigned_hospital": None,
        "assigned_ward": None,
        "assigned_bed": None,
        "reallocated_patients": []
    }

    is_high_risk = patient["is_post_surgery"]
    target_models = [4] if is_high_risk else [1, 2, 3, 4]

    for hospital in hospitals:
        if hospital["model"] in target_models:
            for ward in hospital["wards"]:
                if is_ward_suitable(patient, ward):
                    if ward["available_beds"]:
                        result["assigned_hospital"] = hospital["id"]
                        result["assigned_ward"] = ward["ward_name"]
                        result["assigned_bed"] = min(ward["available_beds"])
                        return result

    if is_high_risk:
        for hospital in hospitals:
            if hospital["model"] == 4:
                for ward in hospital["wards"]:
                    if is_ward_suitable(patient, ward):
                        for current_patient in ward["current_patients"]:
                            if current_patient["days_in_hospital"] > 3 and not current_patient["non_transferable"]:
                                new_placement = find_new_placement(current_patient, hospitals)
                                if new_placement:
                                    result["assigned_hospital"] = hospital["id"]
                                    result["assigned_ward"] = ward["ward_name"]
                                    result["assigned_bed"] = current_patient["bed_number"]
                                    result["reallocated_patients"].append({
                                        "patient_id": current_patient["id"],
                                        "new_hospital": new_placement["hospital_id"],
                                        "new_ward": new_placement["ward_name"],
                                        "new_bed": new_placement["bed_number"]
                                    })
                                    return result

    return result

def is_ward_suitable(patient, ward):
    gender_ok = ward["gender_restriction"] == "No Restriction" or ward["gender_restriction"] == f"{patient['gender']} Only"
    age_ok = ward["age_restriction"][0] <= patient["age"] <= ward["age_restriction"][1]
    requirements_ok = all(req in ward["special_requirements"] for req in patient["special_requirements"])
    return gender_ok and age_ok and requirements_ok

def find_new_placement(patient, hospitals):
    for hospital in hospitals:
        if hospital["model"] < 4:
            for ward in hospital["wards"]:
                if is_ward_suitable(patient, ward) and ward["available_beds"]:
                    return {
                        "hospital_id": hospital["id"],
                        "ward_name": ward["ward_name"],
                        "bed_number": min(ward["available_beds"])
                    }
    return None

def main():
    input_data = json.loads(sys.stdin.read())
    result = reallocate_bed(input_data["patient"], input_data["hospitals"])
    print(json.dumps(result))

if __name__ == "__main__":
    main()