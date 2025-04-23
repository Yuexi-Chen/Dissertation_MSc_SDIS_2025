def allocate_bed(patient, wards):
    patient_id = patient['id']
    for ward in wards:
        if (ward['target_condition'] == patient['condition'] and
            (ward['gender_restriction'] == 'No Restriction' or 
             ward['gender_restriction'] == 'No Gender Restriction' or 
             (ward['gender_restriction'] == 'Male Only' and patient['gender'] == 'Male') or
             (ward['gender_restriction'] == 'Female Only' and patient['gender'] == 'Female')) and
            ward['age_restriction'][0] <= patient['age'] <= ward['age_restriction'][1] and
            all(req in ward['special_requirements'] for req in patient['special_requirements'])):
            
            if ward['available_beds']:
                assigned_bed = min(ward['available_beds'])
                return {
                    "patient_id": patient_id,
                    "assigned_ward": ward['ward_name'],
                    "assigned_bed": assigned_bed,
                    "assigned_satellite_hospital": None
                }
            
            for i in range(1, ward['overflow_capacity'] + 1):
                overflow_bed_label = f"Overflow-{i}"
                if overflow_bed_label not in ward['available_beds']:
                    return {
                        "patient_id": patient_id,
                        "assigned_ward": ward['ward_name'],
                        "assigned_bed": overflow_bed_label,
                        "assigned_satellite_hospital": None
                    }
            
            if ward['satellite_hospitals']:
                return {
                    "patient_id": patient_id,
                    "assigned_ward": None,
                    "assigned_bed": None,
                    "assigned_satellite_hospital": ward['satellite_hospitals'][0]
                }
    
    return {
        "patient_id": patient_id,
        "assigned_ward": None,
        "assigned_bed": None,
        "assigned_satellite_hospital": None
    }

def main():
    import sys
    import json
    input_data = json.load(sys.stdin)
    result = allocate_bed(input_data['patient'], input_data['wards'])
    print(json.dumps(result))

if __name__ == "__main__":
    main()