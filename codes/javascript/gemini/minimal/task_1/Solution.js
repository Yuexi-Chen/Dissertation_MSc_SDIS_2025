function allocateBed(patient, wards) {
  let result = {
    patient_id: patient.id,
    assigned_ward: null,
    assigned_bed: null,
    assigned_satellite_hospital: null
  };

  for (let ward of wards) {
    let wardMatchesPatient = true;

    if (ward.gender_restriction && ward.gender_restriction !== "Any" && ward.gender_restriction !== patient.gender + " Only") {
      wardMatchesPatient = false;
    }

    if (ward.age_restriction) {
      if (patient.age < ward.age_restriction[0] || patient.age > ward.age_restriction[1]) {
        wardMatchesPatient = false;
      }
    }

    if (ward.target_condition !== patient.condition) {
      wardMatchesPatient = false;
    }
    
    if (ward.special_requirements) {
        for (let req of ward.special_requirements) {
            if (!patient.special_requirements.includes(req)) {
                wardMatchesPatient = false;
                break;
            }
        }
    }

    if (wardMatchesPatient) {
      // Step 1: Regular Beds
      if (ward.available_beds && ward.available_beds.length > 0) {
        ward.available_beds.sort((a, b) => a - b);
        result.assigned_ward = ward.ward_name;
        result.assigned_bed = ward.available_beds.shift();
        return result;
      }

      // Step 2: Overflow Beds
      if (ward.overflow_capacity > 0) {
        result.assigned_ward = ward.ward_name;
        result.assigned_bed = `Overflow-${ward.overflow_capacity}`;
        ward.overflow_capacity--;
        return result;
      }

      // Step 3: Satellite Hospitals
      if (ward.satellite_hospitals && ward.satellite_hospitals.length > 0) {
        result.assigned_satellite_hospital = ward.satellite_hospitals[0];
        result.assigned_ward = null;
        result.assigned_bed = null;
        return result;
      }
    }
  }

  return result;
}