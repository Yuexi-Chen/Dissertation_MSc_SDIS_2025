function allocateBed(patient, wards) {
    for (let ward of wards) {
        // Check if the ward matches all patient criteria
        if (
            (ward.gender_restriction === "Any" || ward.gender_restriction === patient.gender || !ward.gender_restriction) &&
            patient.age >= ward.age_restriction[0] &&
            patient.age <= ward.age_restriction[1] &&
            ward.target_condition === patient.condition &&
            ward.special_requirements.every(req => patient.special_requirements.includes(req))
        ) {
            // Step 1: Try to assign a regular bed
            if (ward.available_beds.length > 0) {
                return {
                    patient_id: patient.id,
                    assigned_ward: ward.ward_name,
                    assigned_bed: ward.available_beds[0],
                    assigned_satellite_hospital: null
                };
            }
            // Step 2: Try to assign an overflow bed
            else if (ward.overflow_capacity > 0) {
                return {
                    patient_id: patient.id,
                    assigned_ward: ward.ward_name,
                    assigned_bed: `Overflow-1`,
                    assigned_satellite_hospital: null
                };
            }
            // Step 3: Try to assign a satellite hospital
            else if (ward.satellite_hospitals.length > 0) {
                return {
                    patient_id: patient.id,
                    assigned_ward: null,
                    assigned_bed: null,
                    assigned_satellite_hospital: ward.satellite_hospitals[0]
                };
            }
        }
    }
    // Step 4: No assignment possible
    return {
        patient_id: patient.id,
        assigned_ward: null,
        assigned_bed: null,
        assigned_satellite_hospital: null
    };
}

function main() {
    const fs = require('fs');
    const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
    const result = allocateBed(input.patient, input.wards);
    console.log(JSON.stringify(result));
}

main();