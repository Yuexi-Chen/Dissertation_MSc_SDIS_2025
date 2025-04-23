function allocateBed(patient, wards) {
    const result = {
        patient_id: patient.id,
        assigned_ward: null,
        assigned_bed: null,
        assigned_satellite_hospital: null
    };

    for (const ward of wards) {
        if (ward.target_condition !== patient.condition) continue;
        if (!(ward.gender_restriction === "No Restriction" || 
              ward.gender_restriction === "No Gender Restriction" || 
              ward.gender_restriction === "Male Only" && patient.gender === "Male" || 
              ward.gender_restriction === "Female Only" && patient.gender === "Female")) continue;
        
        if (patient.age < ward.age_restriction[0] || patient.age > ward.age_restriction[1]) continue;
        
        if (!patient.special_requirements.every(req => ward.special_requirements.includes(req))) continue;

        if (ward.available_beds.length > 0) {
            result.assigned_ward = ward.ward_name;
            result.assigned_bed = Math.min(...ward.available_beds);
            return result;
        }

        if (ward.overflow_capacity > 0) {
            result.assigned_ward = ward.ward_name;
            result.assigned_bed = `Overflow-${ward.overflow_capacity}`;
            return result;
        }

        if (ward.satellite_hospitals.length > 0) {
            result.assigned_ward = null;
            result.assigned_bed = null;
            result.assigned_satellite_hospital = ward.satellite_hospitals[0];
            return result;
        }
    }

    return result;
}

const fs = require('fs');

function main() {
    const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
    const patient = input.patient;
    const wards = input.wards;

    const result = allocateBed(patient, wards);
    console.log(JSON.stringify(result));
}

main();