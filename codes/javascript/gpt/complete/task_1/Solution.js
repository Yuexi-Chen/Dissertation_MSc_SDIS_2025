function allocateBed(patient, wards) {
    const patient_id = patient.id;

    for (let ward of wards) {
        const genderMatches = (ward.gender_restriction === "No Restriction" || ward.gender_restriction === "No Gender Restriction" || ward.gender_restriction === `${patient.gender} Only`);
        const ageMatches = (patient.age >= ward.age_restriction[0] && patient.age <= ward.age_restriction[1]);
        const conditionMatches = (ward.target_condition === patient.condition);
        const specialRequirements = patient.special_requirements || [];
        const specialRequirementsMatch = specialRequirements.every(req => ward.special_requirements.includes(req));

        if (genderMatches && ageMatches && conditionMatches && specialRequirementsMatch) {
            if (ward.available_beds.length > 0) {
                const assigned_bed = Math.min(...ward.available_beds);
                return {
                    patient_id,
                    assigned_ward: ward.ward_name,
                    assigned_bed: assigned_bed,
                    assigned_satellite_hospital: null
                };
            } else if (ward.overflow_capacity > 0) {
                return {
                    patient_id,
                    assigned_ward: ward.ward_name,
                    assigned_bed: `Overflow-1`,
                    assigned_satellite_hospital: null
                };
            } else if (ward.satellite_hospitals.length > 0) {
                return {
                    patient_id,
                    assigned_ward: null,
                    assigned_bed: null,
                    assigned_satellite_hospital: ward.satellite_hospitals[0]
                };
            }
        }
    }

    return {
        patient_id,
        assigned_ward: null,
        assigned_bed: null,
        assigned_satellite_hospital: null
    };
}

const fs = require('fs');

let input = '';
process.stdin.on('data', function (chunk) {
    input += chunk;
});

process.stdin.on('end', function () {
    const { patient, wards } = JSON.parse(input);
    const result = allocateBed(patient, wards);
    console.log(JSON.stringify(result));
});