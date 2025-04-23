function reallocateBed(patient, hospitals) {
    function matchesRequirements(patient, ward) {
        if (ward.gender_restriction !== "No Restriction" && ward.gender_restriction !== patient.gender) {
            return false;
        }
        if (patient.age < ward.age_restriction[0] || patient.age > ward.age_restriction[1]) {
            return false;
        }
        for (let req of patient.special_requirements) {
            if (!ward.special_requirements.includes(req)) {
                return false;
            }
        }
        return true;
    }

    function findAvailableBed(hospitals, patient, modelPriority) {
        for (let hospital of hospitals) {
            if (modelPriority.includes(hospital.model)) {
                for (let ward of hospital.wards) {
                    if (matchesRequirements(patient, ward)) {
                        if (ward.available_beds.length > 0) {
                            return {
                                assigned_hospital: hospital.id,
                                assigned_ward: ward.ward_name,
                                assigned_bed: ward.available_beds.shift(),
                                reallocated_patients: []
                            };
                        }
                    }
                }
            }
        }
        return null;
    }

    function tryReallocateHighRiskPatient(patient, hospitals) {
        for (let hospital of hospitals) {
            if (hospital.model === 4) {
                for (let ward of hospital.wards) {
                    if (matchesRequirements(patient, ward)) {
                        for (let currentPatient of ward.current_patients) {
                            if (currentPatient.days_in_hospital > 3 && !currentPatient.non_transferable) {
                                let newWard = findAvailableBed(hospitals.filter(h => h.model < 4), currentPatient, [1, 2, 3]);
                                if (newWard) {
                                    ward.current_patients = ward.current_patients.filter(p => p.id !== currentPatient.id);
                                    newWard.reallocated_patients.push({
                                        patient_id: currentPatient.id,
                                        new_hospital: newWard.assigned_hospital,
                                        new_ward: newWard.assigned_ward,
                                        new_bed: newWard.assigned_bed
                                    });
                                    return {
                                        assigned_hospital: hospital.id,
                                        assigned_ward: ward.ward_name,
                                        assigned_bed: currentPatient.bed_number,
                                        reallocated_patients: newWard.reallocated_patients
                                    };
                                }
                            }
                        }
                    }
                }
            }
        }
        return null;
    }

    let modelPriority = patient.is_post_surgery ? [4] : [1, 2, 3, 4];
    let directAssignment = findAvailableBed(hospitals, patient, modelPriority);

    if (directAssignment) {
        return {
            patient_id: patient.id,
            ...directAssignment
        };
    }

    if (patient.is_post_surgery) {
        let reallocationResult = tryReallocateHighRiskPatient(patient, hospitals);
        if (reallocationResult) {
            return {
                patient_id: patient.id,
                ...reallocationResult
            };
        }
    }

    return {
        patient_id: patient.id,
        assigned_hospital: null,
        assigned_ward: null,
        assigned_bed: null,
        reallocated_patients: []
    };
}

const fs = require('fs');
const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
const result = reallocateBed(input.patient, input.hospitals);
console.log(JSON.stringify(result));