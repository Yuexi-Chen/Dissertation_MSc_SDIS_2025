def reallocate_bed(patient, hospitals):
    def matches_ward_requirements(patient, ward):
        if ward['gender_restriction'] != 'No Restriction' and ward['gender_restriction'] != patient['gender']:
            return False
        if not (ward['age_restriction'][0] <= patient['age'] <= ward['age_restriction'][1]):
            return False
        if not all(req in ward['special_requirements'] for req in patient['special_requirements']):
            return False
        return True

    def find_available_bed(wards):
        for ward in wards:
            if matches_ward_requirements(patient, ward):
                for bed in sorted(ward['available_beds']):
                    return ward, bed
        return None, None

    def check_reallocation(hospitals):
        reallocated_patients = []
        for hospital in hospitals:
            if hospital['model'] != 4:
                continue
            for ward in hospital['wards']:
                if matches_ward_requirements(patient, ward):
                    transferable_candidates = [
                        p for p in ward['current_patients']
                        if p['days_in_hospital'] > 3 and not p['non_transferable']
                    ]
                    transferable_candidates.sort(key=lambda p: (-p['days_in_hospital'], p['bed_number']))
                    for candidate in transferable_candidates:
                        for target_hospital in hospitals:
                            if target_hospital['model'] < 4:
                                for target_ward in target_hospital['wards']:
                                    if matches_ward_requirements(candidate, target_ward):
                                        if target_ward['available_beds']:
                                            new_bed = min(target_ward['available_beds'])
                                            target_ward['available_beds'].remove(new_bed)
                                            reallocated_patients.append({
                                                'patient_id': candidate['id'],
                                                'new_hospital': target_hospital['id'],
                                                'new_ward': target_ward['ward_name'],
                                                'new_bed': new_bed
                                            })
                                            return ward, candidate['bed_number'], reallocated_patients
        return None, None, []

    if patient['is_post_surgery']:
        # High-risk patient
        wards = []
        for hospital in hospitals:
            if hospital['model'] == 4:
                wards.extend(hospital['wards'])
        ward, bed = find_available_bed(wards)
        if ward and bed:
            return {
                "patient_id": patient['id'],
                "assigned_hospital": hospitals[0]['id'],
                "assigned_ward": ward['ward_name'],
                "assigned_bed": bed,
                "reallocated_patients": []
            }
        else:
            ward, bed, reallocated_patients = check_reallocation(hospitals)
            if ward and bed:
                return {
                    "patient_id": patient['id'],
                    "assigned_hospital": hospitals[0]['id'],
                    "assigned_ward": ward['ward_name'],
                    "assigned_bed": bed,
                    "reallocated_patients": reallocated_patients
                }

    else:
        # Non-high-risk patient
        for hospital in hospitals:
            if hospital['model'] < 4:
                ward, bed = find_available_bed(hospital['wards'])
                if ward and bed:
                    return {
                        "patient_id": patient['id'],
                        "assigned_hospital": hospital['id'],
                        "assigned_ward": ward['ward_name'],
                        "assigned_bed": bed,
                        "reallocated_patients": []
                    }
        # If no beds in lower model hospitals, try model 4
        for hospital in hospitals:
            if hospital['model'] == 4:
                ward, bed = find_available_bed(hospital['wards'])
                if ward and bed:
                    return {
                        "patient_id": patient['id'],
                        "assigned_hospital": hospital['id'],
                        "assigned_ward": ward['ward_name'],
                        "assigned_bed": bed,
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
    result = reallocate_bed(input_data['patient'], input_data['hospitals'])
    print(json.dumps(result))

if __name__ == "__main__":
    main()