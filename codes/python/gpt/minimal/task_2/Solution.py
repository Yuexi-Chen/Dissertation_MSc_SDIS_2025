def reallocate_bed(patient, hospitals):
    def can_assign_to_ward(patient, ward):
        if ward['gender_restriction'] != "No Restriction" and ward['gender_restriction'] != patient['gender']:
            return False
        if not (ward['age_restriction'][0] <= patient['age'] <= ward['age_restriction'][1]):
            return False
        for requirement in patient['special_requirements']:
            if requirement not in ward['special_requirements']:
                return False
        return True

    def find_available_bed(ward):
        if ward['available_beds']:
            return min(ward['available_beds'])
        else:
            return None

    def can_transfer_patient(patient, ward):
        return (not patient['non_transferable'] and
                patient['days_in_hospital'] > 3 and
                can_assign_to_ward(patient, ward))

    # Initialize the result object
    result = {
        "patient_id": patient["id"],
        "assigned_hospital": None,
        "assigned_ward": None,
        "assigned_bed": None,
        "reallocated_patients": []
    }

    # Attempt direct assignment
    for hospital in sorted(hospitals, key=lambda h: h['model']):
        if patient['is_post_surgery'] and hospital['model'] != 4:
            continue
        for ward in hospital['wards']:
            if can_assign_to_ward(patient, ward):
                available_bed = find_available_bed(ward)
                if available_bed is not None:
                    result.update({
                        "assigned_hospital": hospital['id'],
                        "assigned_ward": ward['ward_name'],
                        "assigned_bed": available_bed
                    })
                    return result

    # Attempt reallocation for high-risk patients in Model 4 hospitals
    if patient['is_post_surgery']:
        for hospital in hospitals:
            if hospital['model'] == 4:
                for ward in hospital['wards']:
                    if can_assign_to_ward(patient, ward):
                        # Sort patients by bed number for processing
                        current_patients = sorted(ward['current_patients'], key=lambda p: p['bed_number'])
                        for current_patient in current_patients:
                            if can_transfer_patient(current_patient, ward):
                                # Try transferring the patient to a lower model hospital
                                for target_hospital in sorted(hospitals, key=lambda h: h['model']):
                                    if target_hospital['model'] < 4:
                                        for target_ward in target_hospital['wards']:
                                            if can_assign_to_ward(current_patient, target_ward):
                                                target_bed = find_available_bed(target_ward)
                                                if target_bed is not None:
                                                    # Perform the transfer
                                                    ward['current_patients'].remove(current_patient)
                                                    target_ward['available_beds'].remove(target_bed)
                                                    target_ward['current_patients'].append(current_patient)

                                                    result.update({
                                                        "assigned_hospital": hospital['id'],
                                                        "assigned_ward": ward['ward_name'],
                                                        "assigned_bed": current_patient['bed_number']
                                                    })

                                                    result['reallocated_patients'].append({
                                                        "patient_id": current_patient['id'],
                                                        "new_hospital": target_hospital['id'],
                                                        "new_ward": target_ward['ward_name'],
                                                        "new_bed": target_bed
                                                    })

                                                    return result

    # If no assignment possible, return the result with null values
    return result

def main():
    import sys
    import json

    input_data = json.load(sys.stdin)
    patient = input_data["patient"]
    hospitals = input_data["hospitals"]

    result = reallocate_bed(patient, hospitals)
    print(json.dumps(result))

if __name__ == "__main__":
    main()