function reallocateBed(patient, hospitals) {
    let assigned_hospital = null;
    let assigned_ward = null;
    let assigned_bed = null;
    const reallocated_patients = [];

    const isHighRisk = patient.is_post_surgery;

    // Function to check if a ward matches the patient's requirements
    const wardMatchesPatient = (ward, patient) => {
        if (ward.gender_restriction !== "No Restriction" && ward.gender_restriction !== patient.gender) {
            return false;
        }
        if (patient.age < ward.age_restriction[0] || patient.age > ward.age_restriction[1]) {
            return false;
        }
        if (patient.special_requirements) {
            for (const requirement of patient.special_requirements) {
                if (!ward.special_requirements.includes(requirement)) {
                    return false;
                }
            }
        }
        return true;
    };

    // Function to find available bed in a ward
    const findAvailableBed = (ward) => {
        if (ward.available_beds && ward.available_beds.length > 0) {
            ward.available_beds.sort((a, b) => a - b); // Sort beds in ascending order
            return ward.available_beds[0];
        }
        return null;
    };

    // Function to find the lowest numbered available bed in a ward
    const findLowestAvailableBed = (ward) => {
        if (!ward.available_beds || ward.available_beds.length === 0) return null;
        ward.available_beds.sort((a, b) => a - b);
        return ward.available_beds[0];
    };

    // Direct Assignment Attempt
    for (const hospital of hospitals) {
        if (isHighRisk && hospital.model !== 4) continue;
        if (!isHighRisk && hospital.model === 4) continue;

        for (const ward of hospital.wards) {
            if (wardMatchesPatient(ward, patient)) {
                const availableBed = findAvailableBed(ward);
                if (availableBed !== null) {
                    assigned_hospital = hospital.id;
                    assigned_ward = ward.ward_name;
                    assigned_bed = availableBed;
                    return {
                        patient_id: patient.id,
                        assigned_hospital: assigned_hospital,
                        assigned_ward: assigned_ward,
                        assigned_bed: assigned_bed,
                        reallocated_patients: reallocated_patients,
                    };
                }
            }
        }
    }

    // Reallocation Attempt (Only for High-Risk Patients)
    if (isHighRisk) {
        for (const hospital of hospitals) {
            if (hospital.model !== 4) continue;

            for (const ward of hospital.wards) {
                if (wardMatchesPatient(ward, patient)) {
                    const occupiedBeds = ward.current_patients;
                    if (occupiedBeds) {
                        occupiedBeds.sort((a, b) => a.bed_number - b.bed_number); // Sort occupied beds by bed number

                        for (const occupiedBed of occupiedBeds) {
                            if (occupiedBed.days_in_hospital > 3 && !occupiedBed.non_transferable) {
                                // Try to find a lower-level hospital for the current patient
                                for (const lowerLevelHospital of hospitals) {
                                    if (lowerLevelHospital.model >= 4) continue; // Skip Model 4 hospitals
                                    for (const lowerLevelWard of lowerLevelHospital.wards) {
                                        if (wardMatchesPatient(lowerLevelWard, occupiedBed)) {
                                            const lowestAvailableBed = findLowestAvailableBed(lowerLevelWard);
                                            if (lowestAvailableBed !== null) {
                                                // Reallocate the existing patient
                                                reallocated_patients.push({
                                                    patient_id: occupiedBed.id,
                                                    new_hospital: lowerLevelHospital.id,
                                                    new_ward: lowerLevelWard.ward_name,
                                                    new_bed: lowestAvailableBed,
                                                });

                                                // Assign the high-risk patient to the freed bed
                                                assigned_hospital = hospital.id;
                                                assigned_ward = ward.ward_name;
                                                assigned_bed = occupiedBed.bed_number;

                                                return {
                                                    patient_id: patient.id,
                                                    assigned_hospital: assigned_hospital,
                                                    assigned_ward: assigned_ward,
                                                    assigned_bed: assigned_bed,
                                                    reallocated_patients: reallocated_patients,
                                                };
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // No Assignment Possible
    return {
        patient_id: patient.id,
        assigned_hospital: null,
        assigned_ward: null,
        assigned_bed: null,
        reallocated_patients: [],
    };
}