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

    def is_ward_suitable(ward, patient):
        return (
            (ward["gender_restriction"] == "No Restriction" or ward["gender_restriction"] == f"{patient['gender']} Only") and
            ward["age_restriction"][0] <= patient["age"] <= ward["age_restriction"][1] and
            all(req in ward["special_requirements"] for req in patient["special_requirements"])
        )

    def find_direct_assignment(patient, hospitals):
        for hospital in hospitals:
            if patient["is_post_surgery"] and hospital["model"] != 4:
                continue
            if not patient["is_post_surgery"] and hospital["model"] == 4:
                continue
            for ward in hospital["wards"]:
                if is_ward_suitable(ward, patient):
                    for bed in sorted(ward["available_beds"]):
                        return hospital["id"], ward["ward_name"], bed
        return None, None, None

    def find_reallocation(patient, hospitals):
        for hospital in hospitals:
            if hospital["model"] != 4:
                continue
            for ward in hospital["wards"]:
                if is_ward_suitable(ward, patient):
                    for current_patient in ward["current_patients"]:
                        if current_patient["days_in_hospital"] > 3 and not current_patient["non_transferable"]:
                            for lower_hospital in hospitals:
                                if lower_hospital["model"] < 4:
                                    for lower_ward in lower_hospital["wards"]:
                                        if is_ward_suitable(lower_ward, current_patient) and lower_ward["available_beds"]:
                                            new_bed = min(lower_ward["available_beds"])
                                            return (
                                                hospital["id"],
                                                ward["ward_name"],
                                                current_patient["bed_number"],
                                                {
                                                    "patient_id": current_patient["id"],
                                                    "new_hospital": lower_hospital["id"],
                                                    "new_ward": lower_ward["ward_name"],
                                                    "new_bed": new_bed
                                                }
                                            )
        return None, None, None, None

    assigned_hospital, assigned_ward, assigned_bed = find_direct_assignment(patient, hospitals)

    if assigned_hospital:
        result["assigned_hospital"] = assigned_hospital
        result["assigned_ward"] = assigned_ward
        result["assigned_bed"] = assigned_bed
    elif patient["is_post_surgery"]:
        assigned_hospital, assigned_ward, assigned_bed, reallocated = find_reallocation(patient, hospitals)
        if assigned_hospital:
            result["assigned_hospital"] = assigned_hospital
            result["assigned_ward"] = assigned_ward
            result["assigned_bed"] = assigned_bed
            result["reallocated_patients"].append(reallocated)

    return result

def main():
    input_data = json.loads(sys.stdin.read())
    output = reallocate_bed(input_data["patient"], input_data["hospitals"])
    print(json.dumps(output))

if __name__ == "__main__":
    main()