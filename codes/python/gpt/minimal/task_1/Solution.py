def allocate_bed(patient, wards):
    patient_id = patient['id']
    assigned_ward = None
    assigned_bed = None
    assigned_satellite_hospital = None

    for ward in wards:
        if (ward['gender_restriction'] == 'Any' or patient['gender'] == ward['gender_restriction']) and \
           (ward['age_restriction'][0] <= patient['age'] <= ward['age_restriction'][1]) and \
           (ward['target_condition'] == patient['condition']) and \
           all(req in ward['special_requirements'] for req in patient['special_requirements']):
            
            if ward['available_beds']:
                assigned_ward = ward['ward_name']
                assigned_bed = ward['available_beds'].pop(0)
                break
            elif ward['overflow_capacity'] > 0:
                assigned_ward = ward['ward_name']
                assigned_bed = f"Overflow-{ward['overflow_capacity']}"
                ward['overflow_capacity'] -= 1
                break
            elif ward['satellite_hospitals']:
                assigned_satellite_hospital = ward['satellite_hospitals'][0]
                break

    return {
        "patient_id": patient_id,
        "assigned_ward": assigned_ward,
        "assigned_bed": assigned_bed,
        "assigned_satellite_hospital": assigned_satellite_hospital
    }

def main():
    import sys
    import json
    input_data = json.load(sys.stdin)
    result = allocate_bed(input_data['patient'], input_data['wards'])
    print(json.dumps(result))

if __name__ == "__main__":
    main()