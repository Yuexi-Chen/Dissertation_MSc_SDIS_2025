import json
import sys

def allocate_bed(patient, wards):
    for ward in wards:
        if match_ward(patient, ward):
            # Try regular beds
            if ward['available_beds']:
                return {
                    'patient_id': patient['id'],
                    'assigned_ward': ward['ward_name'],
                    'assigned_bed': min(ward['available_beds']),
                    'assigned_satellite_hospital': None
                }
            
            # Try overflow beds
            if ward['overflow_capacity'] > 0:
                return {
                    'patient_id': patient['id'],
                    'assigned_ward': ward['ward_name'],
                    'assigned_bed': f"Overflow-{ward['overflow_capacity']}",
                    'assigned_satellite_hospital': None
                }
            
            # Try satellite hospitals
            if ward['satellite_hospitals']:
                return {
                    'patient_id': patient['id'],
                    'assigned_ward': None,
                    'assigned_bed': None,
                    'assigned_satellite_hospital': ward['satellite_hospitals'][0]
                }
    
    # No assignment possible
    return {
        'patient_id': patient['id'],
        'assigned_ward': None,
        'assigned_bed': None,
        'assigned_satellite_hospital': None
    }

def match_ward(patient, ward):
    if patient['condition'] != ward['target_condition']:
        return False
    
    if ward['gender_restriction'] not in ['No Restriction', 'No Gender Restriction']:
        if patient['gender'] == 'Male' and ward['gender_restriction'] != 'Male Only':
            return False
        if patient['gender'] == 'Female' and ward['gender_restriction'] != 'Female Only':
            return False
    
    if not (ward['age_restriction'][0] <= patient['age'] <= ward['age_restriction'][1]):
        return False
    
    if not set(patient['special_requirements']).issubset(set(ward['special_requirements'])):
        return False
    
    return True

def main():
    input_data = json.loads(sys.stdin.read())
    result = allocate_bed(input_data['patient'], input_data['wards'])
    print(json.dumps(result))

if __name__ == "__main__":
    main()