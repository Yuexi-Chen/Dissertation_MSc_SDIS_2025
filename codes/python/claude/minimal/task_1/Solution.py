import json
import sys

def allocate_bed(patient, wards):
    for ward in wards:
        if (ward['gender_restriction'] == 'Male Only' and patient['gender'] != 'Male') or \
           (ward['gender_restriction'] == 'Female Only' and patient['gender'] != 'Female') or \
           (patient['age'] < ward['age_restriction'][0] or patient['age'] > ward['age_restriction'][1]) or \
           (ward['target_condition'] != patient['condition']) or \
           (not all(req in ward['special_requirements'] for req in patient['special_requirements'])):
            continue

        # Step 1: Regular beds
        if ward['available_beds']:
            return {
                'patient_id': patient['id'],
                'assigned_ward': ward['ward_name'],
                'assigned_bed': min(ward['available_beds']),
                'assigned_satellite_hospital': None
            }

        # Step 2: Overflow beds
        if ward['overflow_capacity'] > 0:
            return {
                'patient_id': patient['id'],
                'assigned_ward': ward['ward_name'],
                'assigned_bed': f"Overflow-{ward['overflow_capacity']}",
                'assigned_satellite_hospital': None
            }

        # Step 3: Satellite hospitals
        if ward['satellite_hospitals']:
            return {
                'patient_id': patient['id'],
                'assigned_ward': None,
                'assigned_bed': None,
                'assigned_satellite_hospital': ward['satellite_hospitals'][0]
            }

    # Step 4: No assignment
    return {
        'patient_id': patient['id'],
        'assigned_ward': None,
        'assigned_bed': None,
        'assigned_satellite_hospital': None
    }

def main():
    input_data = json.loads(sys.stdin.read())
    result = allocate_bed(input_data['patient'], input_data['wards'])
    print(json.dumps(result))

if __name__ == "__main__":
    main()