function reallocateBed(patient, hospitals) {
    function matchesWard(patient, ward) {
        const genderMatch = ward.gender_restriction === 'No Restriction' || 
            (patient.gender === 'Male' && ward.gender_restriction === 'Male Only') ||
            (patient.gender === 'Female' && ward.gender_restriction === 'Female Only');
        const ageMatch = patient.age >= ward.age_restriction[0] && patient.age <= ward.age_restriction[1];
        const specialMatch = patient.special_requirements.every(requirement => 
            ward.special_requirements.includes(requirement)
        );
        return genderMatch && ageMatch && specialMatch;
    }

    function findAndAssignBed(patient, hospitals, model4Only) {
        for (const hospital of hospitals) {
            if (model4Only && hospital.model !== 4) continue;
            if (!model4Only && hospital.model === 4) continue;
            for (const ward of hospital.wards) {
                if (matchesWard(patient, ward) && ward.available_beds.length > 0) {
                    const assignedBed = ward.available_beds.sort((a, b) => a - b)[0];
                    return {
                        patient_id: patient.id,
                        assigned_hospital: hospital.id,
                        assigned_ward: ward.ward_name,
                        assigned_bed: assignedBed,
                        reallocated_patients: []
                    };
                }
            }
        }
        return null;
    }

    function findReallocation(patient, hospitals) {
        const candidates = [];
        for (const hospital of hospitals) {
            if (hospital.model !== 4) continue;
            for (const ward of hospital.wards) {
                if (matchesWard(patient, ward)) {
                    for (const currentPatient of ward.current_patients) {
                        if (currentPatient.days_in_hospital > 3 && !currentPatient.non_transferable) {
                            candidates.push({
                                currentPatient,
                                hospital,
                                ward
                            });
                        }
                    }
                }
            }
        }

        candidates.sort((a, b) => {
            if (a.currentPatient.days_in_hospital !== b.currentPatient.days_in_hospital) {
                return b.currentPatient.days_in_hospital - a.currentPatient.days_in_hospital;
            }
            return a.currentPatient.bed_number - b.currentPatient.bed_number;
        });

        for (const candidate of candidates) {
            const { currentPatient, hospital, ward } = candidate;
            for (const targetHospital of hospitals) {
                if (targetHospital.model >= hospital.model) continue;
                for (const targetWard of targetHospital.wards) {
                    if (matchesWard(currentPatient, targetWard) && targetWard.available_beds.length > 0) {
                        const newBed = targetWard.available_beds.sort((a, b) => a - b)[0];
                        return {
                            patient_id: patient.id,
                            assigned_hospital: hospital.id,
                            assigned_ward: ward.ward_name,
                            assigned_bed: currentPatient.bed_number,
                            reallocated_patients: [{
                                patient_id: currentPatient.id,
                                new_hospital: targetHospital.id,
                                new_ward: targetWard.ward_name,
                                new_bed: newBed
                            }]
                        };
                    }
                }
            }
        }
        return null;
    }

    if (patient.is_post_surgery) {
        const directAssignment = findAndAssignBed(patient, hospitals, true);
        if (directAssignment) return directAssignment;

        const reallocation = findReallocation(patient, hospitals);
        if (reallocation) return reallocation;
    } else {
        const directAssignment = findAndAssignBed(patient, hospitals, false);
        if (directAssignment) return directAssignment;
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