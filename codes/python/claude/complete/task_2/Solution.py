import json
import sys

def reallocate_bed(patient, hospitals):
    def is_ward_suitable(ward, patient):
        gender_match = ward['gender_restriction'] == 'No Restriction' or \
                       (ward['gender_restriction'] == 'Male Only' and patient['gender'] == 'Male') or \
                       (ward['gender_restriction'] == 'Female Only' and patient['gender'] == 'Female')
        age_match = ward['age_restriction'][0] <= patient['age'] <= ward['age_restriction'][1]
        requirements_match = all(req in ward['special_requirements'] for req in patient['special_requirements'])
        return gender_match and age_match and requirements_match

    def find_direct_assignment(patient, hospitals):
        for hospital in hospitals:
            if patient['is_post_surgery'] and hospital['model'] != 4:
                continue
            if not patient['is_post_surgery'] and hospital['model'] == 4:
                continue
            for ward in hospital['wards']:
                if is_ward_suitable(ward, patient) and ward['available_beds']:
                    return hospital['id'], ward['ward_name'], min(ward['available_beds'])
        return None, None, None

    def find_reallocation(patient, hospitals):
        for hospital in hospitals:
            if hospital['model'] != 4:
                continue
            for ward in hospital['wards']:
                if not is_ward_suitable(ward, patient):
                    continue
                transferable_patients = sorted(
                    [p for p in ward['current_patients'] if p['days_in_hospital'] > 3 and not p['non_transferable']],
                    key=lambda x: (-x['days_in_hospital'], x['bed_number'])
                )
                for tp in transferable_patients:
                    new_assignment = find_direct_assignment(tp, [h for h in hospitals if h['model'] < 4])
                    if new_assignment[0]:
                        return hospital['id'], ward['ward_name'], tp['bed_number'], tp, new_assignment
        return None, None, None, None, None

    assigned_hospital, assigned_ward, assigned_bed = find_direct_assignment(patient, hospitals)
    reallocated_patients = []

    if not assigned_hospital and patient['is_post_surgery']:
        assigned_hospital, assigned_ward, assigned_bed, transferable_patient, new_assignment = find_reallocation(patient, hospitals)
        if assigned_hospital:
            reallocated_patients.append({
                "patient_id": transferable_patient['id'],
                "new_hospital": new_assignment[0],
                "new_ward": new_assignment[1],
                "new_bed": new_assignment[2]
            })

    return {
        "patient_id": patient['id'],
        "assigned_hospital": assigned_hospital,
        "assigned_ward": assigned_ward,
        "assigned_bed": assigned_bed,
        "reallocated_patients": reallocated_patients
    }

def main():
    input_data = json.loads(sys.stdin.read())
    result = reallocate_bed(input_data['patient'], input_data['hospitals'])
    print(json.dumps(result))

if __name__ == "__main__":
    main()