function allocateBed(patient, wards) {
    for (let ward of wards) {
        if (matchesWard(patient, ward)) {
            // Try regular bed
            if (ward.available_beds.length > 0) {
                return {
                    patient_id: patient.id,
                    assigned_ward: ward.ward_name,
                    assigned_bed: Math.min(...ward.available_beds),
                    assigned_satellite_hospital: null
                };
            }
            
            // Try overflow bed
            if (ward.overflow_capacity > 0) {
                return {
                    patient_id: patient.id,
                    assigned_ward: ward.ward_name,
                    assigned_bed: `Overflow-${ward.overflow_capacity}`,
                    assigned_satellite_hospital: null
                };
            }
            
            // Try satellite hospital
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
        patient.condition === ward.target_condition &&
        matchesGender(patient.gender, ward.gender_restriction) &&
        patient.age >= ward.age_restriction[0] &&
        patient.age <= ward.age_restriction[1] &&
        matchesSpecialRequirements(patient.special_requirements, ward.special_requirements)
    );
}

function matchesGender(patientGender, wardGenderRestriction) {
    if (wardGenderRestriction === "No Restriction" || wardGenderRestriction === "No Gender Restriction") {
        return true;
    }
    return (patientGender === "Male" && wardGenderRestriction === "Male Only") ||
           (patientGender === "Female" && wardGenderRestriction === "Female Only");
}

function matchesSpecialRequirements(patientRequirements, wardRequirements) {
    if (!patientRequirements || patientRequirements.length === 0) {
        return true;
    }
    return patientRequirements.every(req => wardRequirements.includes(req));
}

// Read input from stdin
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const result = allocateBed(input.patient, input.wards);
console.log(JSON.stringify(result));