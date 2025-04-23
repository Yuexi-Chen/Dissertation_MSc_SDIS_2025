function allocateBed(patient, wards) {
  let result = {
    patient_id: patient.id,
    assigned_ward: null,
    assigned_bed: null,
    assigned_satellite_hospital: null,
  };

  for (const ward of wards) {
    // Ward Matching
    let wardMatches = true;

    // Condition
    if (ward.target_condition !== patient.condition) {
      wardMatches = false;
    }

    // Gender
    if (ward.gender_restriction === "Male Only" && patient.gender !== "Male") {
      wardMatches = false;
    } else if (
      ward.gender_restriction === "Female Only" &&
      patient.gender !== "Female"
    ) {
      wardMatches = false;
    }

    // Age
    if (
      patient.age < ward.age_restriction[0] ||
      patient.age > ward.age_restriction[1]
    ) {
      wardMatches = false;
    }

    // Special Requirements
    for (const requirement of patient.special_requirements) {
      if (!ward.special_requirements.includes(requirement)) {
        wardMatches = false;
        break;
      }
    }

    if (wardMatches) {
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

  // Step 4: No Assignment
  return result;
}

if (typeof process !== 'undefined' && process.argv.length > 2) {
  let inputData = '';
  process.stdin.on('data', (chunk) => {
    inputData += chunk;
  });

  process.stdin.on('end', () => {
    try {
      const input = JSON.parse(inputData);
      const result = allocateBed(input.patient, input.wards);
      console.log(JSON.stringify(result));
    } catch (error) {
      console.error('Error processing input:', error);
    }
  });
}