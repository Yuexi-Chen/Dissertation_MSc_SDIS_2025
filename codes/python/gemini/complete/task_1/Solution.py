def allocate_bed(patient, wards):
    patient_id = patient['id']
    assigned_ward = None
    assigned_bed = None
    assigned_satellite_hospital = None

    for ward in wards:
        # Ward Matching
        if ward['target_condition'] != patient['condition']:
            continue

        gender_restriction = ward['gender_restriction']
        if gender_restriction == 'Male Only' and patient['gender'] != 'Male':
            continue
        if gender_restriction == 'Female Only' and patient['gender'] != 'Female':
            continue
        if gender_restriction not in ('No Restriction', 'No Gender Restriction') and \
           gender_restriction != patient['gender']:
            continue

        age_restriction = ward['age_restriction']
        if not (age_restriction[0] <= patient['age'] <= age_restriction[1]):
            continue

        ward_special_requirements = ward.get('special_requirements') or []
        patient_special_requirements = patient.get('special_requirements') or []
        if not all(req in ward_special_requirements for req in patient_special_requirements):
            continue

        # Bed Allocation
        if ward['available_beds']:
            assigned_bed = min(ward['available_beds'])
            ward['available_beds'].remove(assigned_bed)
            assigned_ward = ward['ward_name']
            break
        elif ward['overflow_capacity'] > 0:
            assigned_ward = ward['ward_name']
            overflow_beds_used = 0
            assigned_bed = f"Overflow-{overflow_beds_used + 1}"
            ward['overflow_capacity'] -= 1
            break
        elif ward['satellite_hospitals']:
            assigned_satellite_hospital = ward['satellite_hospitals'][0]
            assigned_ward = None
            assigned_bed = None
            break

    return {
        'patient_id': patient_id,
        'assigned_ward': assigned_ward,
        'assigned_bed': assigned_bed,
        'assigned_satellite_hospital': assigned_satellite_hospital
    }


if __name__ == '__main__':
    import json
    import sys

    input_data = json.load(sys.stdin)
    patient = input_data['patient']
    wards = input_data['wards']

    result = allocate_bed(patient, wards)
    print(json.dumps(result))