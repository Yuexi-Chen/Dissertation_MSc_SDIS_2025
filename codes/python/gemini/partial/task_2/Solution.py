import json

def reallocate_bed(patient, hospitals):
    patient_id = None
    assigned_hospital = None
    assigned_ward = None
    assigned_bed = None
    reallocated_patients = []

    patient_id = patient["id"]
    is_high_risk = patient["is_post_surgery"]

    def find_available_bed(hospital, ward):
        for bed in sorted(ward["available_beds"]):
            return bed
        return None

    def ward_matches_patient(ward, patient):
        if ward["gender_restriction"] != "No Restriction" and ward["gender_restriction"] != patient["gender"]:
            return False
        if not (ward["age_restriction"][0] <= patient["age"] <= ward["age_restriction"][1]):
            return False
        for requirement in patient["special_requirements"]:
            if requirement not in ward["special_requirements"]:
                return False
        return True

    if is_high_risk:
        eligible_hospitals = [h for h in hospitals if h["model"] == 4]
    else:
        eligible_hospitals = hospitals

    for hospital in eligible_hospitals:
        if is_high_risk and hospital["model"] != 4:
            continue
        if not is_high_risk and hospital["model"] == 4:
            continue
        for ward in hospital["wards"]:
            if ward_matches_patient(ward, patient):
                available_bed = find_available_bed(hospital, ward)
                if available_bed:
                    assigned_hospital = hospital["id"]
                    assigned_ward = ward["ward_name"]
                    assigned_bed = available_bed
                    ward["available_beds"].remove(available_bed)
                    return {
                        "patient_id": patient_id,
                        "assigned_hospital": assigned_hospital,
                        "assigned_ward": assigned_ward,
                        "assigned_bed": assigned_bed,
                        "reallocated_patients": reallocated_patients,
                    }

    if is_high_risk:
        for hospital in [h for h in hospitals if h["model"] == 4]:
            for ward in hospital["wards"]:
                if ward_matches_patient(ward, patient):
                    for occupied_bed_index in range(len(ward["current_patients"])):
                        occupied_bed = ward["current_patients"][occupied_bed_index]
                        if (
                            occupied_bed["days_in_hospital"] > 3
                            and not occupied_bed["non_transferable"]
                        ):
                            
                            for lower_level_hospital in [h for h in hospitals if h["model"] < 4]:
                                for lower_level_ward in lower_level_hospital["wards"]:
                                    if ward_matches_patient(lower_level_ward, occupied_bed):
                                        available_bed_in_lower_level = None
                                        if lower_level_ward["available_beds"]:
                                            available_bed_in_lower_level = sorted(lower_level_ward["available_beds"])[0]
                                        if available_bed_in_lower_level is not None:
                                            
                                            reallocated_patients.append({
                                                "patient_id": occupied_bed["id"],
                                                "new_hospital": lower_level_hospital["id"],
                                                "new_ward": lower_level_ward["ward_name"],
                                                "new_bed": available_bed_in_lower_level,
                                            })

                                            assigned_hospital = hospital["id"]
                                            assigned_ward = ward["ward_name"]
                                            assigned_bed = occupied_bed["bed_number"]

                                            lower_level_ward["available_beds"].remove(available_bed_in_lower_level)
                                            ward["current_patients"].pop(occupied_bed_index)
                                            
                                            return {
                                                "patient_id": patient_id,
                                                "assigned_hospital": assigned_hospital,
                                                "assigned_ward": assigned_ward,
                                                "assigned_bed": assigned_bed,
                                                "reallocated_patients": reallocated_patients,
                                            }

    return {
        "patient_id": patient_id,
        "assigned_hospital": assigned_hospital,
        "assigned_ward": assigned_ward,
        "assigned_bed": assigned_bed,
        "reallocated_patients": reallocated_patients,
    }


if __name__ == "__main__":
    input_json = json.loads(input())
    result = reallocate_bed(input_json["patient"], input_json["hospitals"])
    print(json.dumps(result))