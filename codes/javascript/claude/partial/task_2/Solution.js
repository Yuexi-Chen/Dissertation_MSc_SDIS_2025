function reallocateBed(patient, hospitals) {
    function isMatchingWard(patient, ward) {
        return (ward.gender_restriction === "No Restriction" || ward.gender_restriction === `${patient.gender} Only`) &&
               patient.age >= ward.age_restriction[0] && patient.age <= ward.age_restriction[1] &&
               patient.special_requirements.every(req => ward.special_requirements.includes(req));
    }

    function findDirectAssignment(patient, hospitals) {
        for (const hospital of hospitals) {
            if (patient.is_post_surgery && hospital.model !== 4) continue;
            if (!patient.is_post_surgery && hospital.model === 4) continue;
            
            for (const ward of hospital.wards) {
                if (isMatchingWard(patient, ward) && ward.available_beds.length > 0) {
                    return {
                        hospital: hospital.id,
                        ward: ward.ward_name,
                        bed: ward.available_beds[0]
                    };
                }
            }
        }
        return null;
    }

    function findReallocation(patient, hospitals) {
        for (const hospital of hospitals) {
            if (hospital.model !== 4) continue;
            
            for (const ward of hospital.wards) {
                if (!isMatchingWard(patient, ward)) continue;
                
                for (const currentPatient of ward.current_patients) {
                    if (currentPatient.days_in_hospital <= 3 || currentPatient.non_transferable) continue;
                    
                    for (const lowerHospital of hospitals) {
                        if (lowerHospital.model === 4) continue;
                        
                        for (const lowerWard of lowerHospital.wards) {
                            if (isMatchingWard(currentPatient, lowerWard) && lowerWard.available_beds.length > 0) {
                                return {
                                    assigned: {
                                        hospital: hospital.id,
                                        ward: ward.ward_name,
                                        bed: currentPatient.bed_number
                                    },
                                    reallocated: {
                                        patient_id: currentPatient.id,
                                        new_hospital: lowerHospital.id,
                                        new_ward: lowerWard.ward_name,
                                        new_bed: lowerWard.available_beds[0]
                                    }
                                };
                            }
                        }
                    }
                }
            }
        }
        return null;
    }

    let result = findDirectAssignment(patient, hospitals);
    if (result) {
        return {
            patient_id: patient.id,
            assigned_hospital: result.hospital,
            assigned_ward: result.ward,
            assigned_bed: result.bed,
            reallocated_patients: []
        };
    }

    if (patient.is_post_surgery) {
        result = findReallocation(patient, hospitals);
        if (result) {
            return {
                patient_id: patient.id,
                assigned_hospital: result.assigned.hospital,
                assigned_ward: result.assigned.ward,
                assigned_bed: result.assigned.bed,
                reallocated_patients: [result.reallocated]
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