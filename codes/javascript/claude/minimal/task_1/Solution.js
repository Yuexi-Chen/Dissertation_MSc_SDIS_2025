function allocateBed(patient, wards) {
    for (let ward of wards) {
        if (matchesWard(patient, ward)) {
            // Try regular beds
            if (ward.available_beds.length > 0) {
                return {
                    patient_id: patient.id,
                    assigned_ward: ward.ward_name,
                    assigned_bed: ward.available_beds[0],
                    assigned_satellite_hospital: null
                };
            }
            
            // Try overflow beds
            if (ward.overflow_capacity > 0) {
                return {
                    patient_id: patient.id,
                    assigned_ward: ward.ward_name,
                    assigned_bed: `Overflow-${ward.overflow_capacity}`,
                    assigned_satellite_hospital: null
                };
            }
            
            // Try satellite hospitals
            if (ward.satellite_hospitals.length > 0) {
                return {
                    patient_id: patient.id,
                    assigned_ward: null,
                    assigned_bed: null,
                    assigned_satellite_hospital: ward.satellite_hospitals[0]
                };
            }
        }
    }
    
    // No assignment possible
    return {
        patient_id: patient.id,
        assigned_ward: null,
        assigned_bed: null,
        assigned_satellite_hospital: null
    };
}

function matchesWard(patient, ward) {
    return (
        (ward.gender_restriction === "Any" || 
         (ward.gender_restriction === "Male Only" && patient.gender === "Male") ||
         (ward.gender_restriction === "Female Only" && patient.gender === "Female")) &&
        patient.age >= ward.age_restriction[0] &&
        patient.age <= ward.age_restriction[1] &&
        patient.condition === ward.target_condition &&
        patient.special_requirements.every(req => ward.special_requirements.includes(req))
    );
}

// Read input from stdin
const input = JSON.parse(require('fs').readFileSync(0, 'utf-8'));
const result = allocateBed(input.patient, input.wards);
console.log(JSON.stringify(result));