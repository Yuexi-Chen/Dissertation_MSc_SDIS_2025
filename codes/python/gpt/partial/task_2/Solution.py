def reallocate_bed(patient, hospitals):
    def matches_ward_requirements(patient, ward):
        gender_matches = ward['gender_restriction'] == 'No Restriction' or ward['gender_restriction'] == patient['gender']
        age_matches = ward['age_restriction'][0] <= patient['age'] <= ward['age_restriction'][1]
        special_matches = all(req in ward['special_requirements'] for req in patient['special_requirements'])
        return gender_matches and age_matches and special_matches

    def find_bed_in_hospital(hospital, patient):
        for ward in hospital['wards']:
            if matches_ward_requirements(patient, ward):
                if ward['available_beds']:
                    return hospital['id'], ward['ward_name'], ward['available_beds'][0]
        return None

    def find_transferable_patient(model_1_3_hospitals, transferable_patient):
        for hospital in model_1_3_hospitals:
            for ward in hospital['wards']:
                if matches_ward_requirements(transferable_patient, ward):
                    if ward['available_beds']:
                        return hospital['id'], ward['ward_name'], ward['available_beds'][0]
        return None

    high_risk = patient['is_post_surgery']
    model_4_hospitals = [h for h in hospitals if h['model'] == 4]
    model_1_3_hospitals = [h for h in hospitals if 1 <= h['model'] <= 3]

    if high_risk:
        for hospital in model_4_hospitals:
            result = find_bed_in_hospital(hospital, patient)
            if result:
                hospital_id, ward_name, bed_number = result
                return {
                    "patient_id": patient['id'],
                    "assigned_hospital": hospital_id,
                    "assigned_ward": ward_name,
                    "assigned_bed": bed_number,
                    "reallocated_patients": []
                }

        reallocated_patients = []

        for hospital in model_4_hospitals:
            for ward in hospital['wards']:
                if matches_ward_requirements(patient, ward):
                    for current_patient in sorted(ward['current_patients'], key=lambda x: x['bed_number']):
                        if current_patient['days_in_hospital'] > 3 and not current_patient['non_transferable']:
                            transfer_result = find_transferable_patient(model_1_3_hospitals, current_patient)
                            if transfer_result:
                                new_hospital_id, new_ward_name, new_bed_number = transfer_result
                                reallocated_patients.append({
                                    "patient_id": current_patient['id'],
                                    "new_hospital": new_hospital_id,
                                    "new_ward": new_ward_name,
                                    "new_bed": new_bed_number
                                })
                                return {
                                    "patient_id": patient['id'],
                                    "assigned_hospital": hospital['id'],
                                    "assigned_ward": ward['ward_name'],
                                    "assigned_bed": current_patient['bed_number'],
                                    "reallocated_patients": reallocated_patients
                                }

    else:
        for hospital in model_1_3_hospitals:
            result = find_bed_in_hospital(hospital, patient)
            if result:
                hospital_id, ward_name, bed_number = result
                return {
                    "patient_id": patient['id'],
                    "assigned_hospital": hospital_id,
                    "assigned_ward": ward_name,
                    "assigned_bed": bed_number,
                    "reallocated_patients": []
                }

    for hospital in model_4_hospitals:
        result = find_bed_in_hospital(hospital, patient)
        if result:
            hospital_id, ward_name, bed_number = result
            return {
                "patient_id": patient['id'],
                "assigned_hospital": hospital_id,
                "assigned_ward": ward_name,
                "assigned_bed": bed_number,
                "reallocated_patients": []
            }

    return {
        "patient_id": patient['id'],
        "assigned_hospital": None,
        "assigned_ward": None,
        "assigned_bed": None,
        "reallocated_patients": []
    }

def main():
    import sys
    import json
    input_data = json.load(sys.stdin)
    result = reallocate_bed(input_data["patient"], input_data["hospitals"])
    print(json.dumps(result))

if __name__ == "__main__":
    main()