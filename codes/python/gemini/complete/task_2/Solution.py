import json

def reallocate_bed(patient, hospitals):
    patient_id = None
    assigned_hospital = None
    assigned_ward = None
    assigned_bed = None
    reallocated_patients = []

    is_high_risk = patient["is_post_surgery"]

    def ward_matches(ward, patient):
        if ward["gender_restriction"] == "Female Only" and patient["gender"] != "Female":
            return False
        if ward["gender_restriction"] == "Male Only" and patient["gender"] != "Male":
            return False
        if not (ward["age_restriction"][0] <= patient["age"] <= ward["age_restriction"][1]):
            return False
        for requirement in patient["special_requirements"]:
            if requirement not in ward["special_requirements"]:
                return False
        return True

    def find_available_bed(hospital, ward):
        for bed in sorted(ward["available_beds"]):
            return bed
        return None

    def find_suitable_lower_level_hospital(patient, hospitals):
        for hospital in hospitals:
            if hospital["model"] < 4:
                for ward in hospital["wards"]:
                    if ward_matches(ward, patient) and ward["available_beds"]:
                        return hospital, ward, sorted(ward["available_beds"])[0]
        return None, None, None

    if is_high_risk:
        eligible_hospitals = [h for h in hospitals if h["model"] == 4]
    else:
        eligible_hospitals = hospitals

    # Direct Assignment Attempt
    for hospital in eligible_hospitals:
        if is_high_risk or hospital["model"] < 4:
            for ward in hospital["wards"]:
                if ward_matches(ward, patient):
                    available_bed = find_available_bed(hospital, ward)
                    if available_bed:
                        patient_id = patient["id"]
                        assigned_hospital = hospital["id"]
                        assigned_ward = ward["ward_name"]
                        assigned_bed = available_bed
                        return {
                            "patient_id": patient_id,
                            "assigned_hospital": assigned_hospital,
                            "assigned_ward": assigned_ward,
                            "assigned_bed": assigned_bed,
                            "reallocated_patients": reallocated_patients,
                        }
        elif not is_high_risk and hospital["model"] == 4:
            for ward in hospital["wards"]:
                if ward_matches(ward, patient):
                    available_bed = find_available_bed(hospital, ward)
                    if available_bed:
                        patient_id = patient["id"]
                        assigned_hospital = hospital["id"]
                        assigned_ward = ward["ward_name"]
                        assigned_bed = available_bed
                        return {
                            "patient_id": patient_id,
                            "assigned_hospital": assigned_hospital,
                            "assigned_ward": assigned_ward,
                            "assigned_bed": assigned_bed,
                            "reallocated_patients": reallocated_patients,
                        }

    # Reallocation Attempt (only for high-risk patients)
    if is_high_risk:
        for hospital in [h for h in hospitals if h["model"] == 4]:
            for ward in hospital["wards"]:
                occupied_beds = sorted(
                    [p for p in ward["current_patients"] if p["days_in_hospital"] > 3 and not p["non_transferable"]],
                    key=lambda x: (x["days_in_hospital"], x["bed_number"]),
                    reverse=True,
                )

                for transferable_patient in occupied_beds:
                    lower_hospital, lower_ward, lower_bed = find_suitable_lower_level_hospital(transferable_patient, hospitals)
                    if lower_hospital and lower_ward and lower_bed:
                        # Perform the reallocation
                        patient_id = patient["id"]
                        assigned_hospital = hospital["id"]
                        assigned_ward = ward["ward_name"]
                        assigned_bed = transferable_patient["bed_number"]

                        reallocated_patients.append({
                            "patient_id": transferable_patient["id"],
                            "new_hospital": lower_hospital["id"],
                            "new_ward": lower_ward["ward_name"],
                            "new_bed": lower_bed,
                        })

                        return {
                            "patient_id": patient_id,
                            "assigned_hospital": assigned_hospital,
                            "assigned_ward": assigned_ward,
                            "assigned_bed": assigned_bed,
                            "reallocated_patients": reallocated_patients,
                        }

    # No Assignment Possible
    return {
        "patient_id": patient_id,
        "assigned_hospital": assigned_hospital,
        "assigned_ward": assigned_ward,
        "assigned_bed": assigned_bed,
        "reallocated_patients": reallocated_patients,
    }


if __name__ == "__main__":
    import sys

    input_data = json.loads(sys.stdin.read())
    result = reallocate_bed(input_data["patient"], input_data["hospitals"])
    print(json.dumps(result))