import json

def reallocate_bed(patient, hospitals):
    patient_id = patient.get('id')
    patient_gender = patient.get('gender')
    patient_age = patient.get('age')
    patient_is_post_surgery = patient.get('is_post_surgery')
    patient_special_requirements = patient.get('special_requirements')

    assigned_hospital = None
    assigned_ward = None
    assigned_bed = None
    reallocated_patients = []

    def find_matching_wards(hospital, patient):
        matching_wards = []
        for ward in hospital['wards']:
            gender_restriction = ward.get('gender_restriction')
            age_restriction = ward.get('age_restriction')
            special_requirements = ward.get('special_requirements')

            gender_match = (gender_restriction == "No Restriction" or gender_restriction == patient['gender'] + " Only")
            age_match = (age_restriction[0] <= patient['age'] <= age_restriction[1])

            special_requirements_match = all(req in special_requirements for req in patient['special_requirements'])

            if gender_match and age_match and special_requirements_match:
                matching_wards.append(ward)
        return matching_wards

    def direct_assignment(patient, hospitals):
        for hospital in hospitals:
            if patient['is_post_surgery'] and hospital['model'] != 4:
                continue
            if not patient['is_post_surgery'] and hospital['model'] == 4:
                continue

            matching_wards = find_matching_wards(hospital, patient)

            for ward in matching_wards:
                available_beds = sorted(ward.get('available_beds'))
                for bed in available_beds:
                    return hospital['id'], ward['ward_name'], bed
        return None, None, None

    def reallocation(patient, hospitals):
        if not patient['is_post_surgery']:
            return None, []

        for hospital in hospitals:
            if hospital['model'] != 4:
                continue

            for ward in hospital['wards']:
                current_patients = ward.get('current_patients')
                if not current_patients:
                    continue

                for existing_patient in sorted(current_patients, key=lambda x: x.get('bed_number')):
                    if existing_patient['days_in_hospital'] > 3 and not existing_patient['non_transferable']:
                        transfer_patient_id = existing_patient['id']
                        transfer_bed_number = existing_patient['bed_number']

                        for lower_hospital in hospitals:
                            if lower_hospital['model'] >= 4:
                                continue

                            lower_hospital_wards = find_matching_wards(lower_hospital, existing_patient)

                            if not lower_hospital_wards:
                                continue

                            for lower_ward in lower_hospital_wards:
                                available_beds = sorted(lower_ward.get('available_beds'))
                                if available_beds:
                                    new_bed = available_beds[0]
                                    reallocated_patients.append({
                                        'patient_id': transfer_patient_id,
                                        'new_hospital': lower_hospital['id'],
                                        'new_ward': lower_ward['ward_name'],
                                        'new_bed': new_bed
                                    })
                                    return hospital['id'], ward['ward_name'], transfer_bed_number

        return None, []

    assigned_hospital, assigned_ward, assigned_bed = direct_assignment(patient, hospitals)

    if assigned_hospital:
        return {
            'patient_id': patient_id,
            'assigned_hospital': assigned_hospital,
            'assigned_ward': assigned_ward,
            'assigned_bed': assigned_bed,
            'reallocated_patients': []
        }

    assigned_hospital, ward_name, assigned_bed = reallocation(patient, hospitals)
    if assigned_hospital:
        return {
            'patient_id': patient_id,
            'assigned_hospital': assigned_hospital,
            'assigned_ward': ward_name,
            'assigned_bed': assigned_bed,
            'reallocated_patients': reallocated_patients
        }

    return {
        'patient_id': patient_id,
        'assigned_hospital': None,
        'assigned_ward': None,
        'assigned_bed': None,
        'reallocated_patients': []
    }

if __name__ == "__main__":
    import sys

    input_data = json.loads(sys.stdin.read())
    patient = input_data.get('patient')
    hospitals = input_data.get('hospitals')

    result = reallocate_bed(patient, hospitals)
    print(json.dumps(result))