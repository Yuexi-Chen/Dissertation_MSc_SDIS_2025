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
                overflow_bed = f"Overflow-{ward['overflow_capacity']}"
                return {
                    'patient_id': patient['id'],
                    'assigned_ward': ward['ward_name'],
                    'assigned_bed': overflow_bed,
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
    # Check condition
    if patient['condition'] != ward['target_condition']:
        return False
    
    # Check gender
    if ward['gender_restriction'] not in ['No Restriction', 'No Gender Restriction']:
        if (ward['gender_restriction'] == 'Male Only' and patient['gender'] != 'Male') or \
           (ward['gender_restriction'] == 'Female Only' and patient['gender'] != 'Female'):
            return False
    
    # Check age
    if not (ward['age_restriction'][0] <= patient['age'] <= ward['age_restriction'][1]):
        return False
    
    # Check special requirements
    patient_requirements = patient.get('special_requirements', []) or []
    ward_requirements = ward.get('special_requirements', []) or []
    if not set(patient_requirements).issubset(set(ward_requirements)):
        return False
    
    return True

def main():
    input_data = json.loads(sys.stdin.read())
    result = allocate_bed(input_data['patient'], input_data['wards'])
    print(json.dumps(result))

if __name__ == "__main__":
    main()