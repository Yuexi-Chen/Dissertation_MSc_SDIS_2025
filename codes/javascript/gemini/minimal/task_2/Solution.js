function reallocateBed(patient, hospitals) {
  let assigned_hospital = null;
  let assigned_ward = null;
  let assigned_bed = null;
  const reallocated_patients = [];

  const isHighRisk = patient.is_post_surgery;

  // Direct Assignment (First Attempt)
  for (const hospital of hospitals) {
    if (isHighRisk && hospital.model !== 4) continue;
    if (!isHighRisk && hospital.model === 4) continue;

    for (const ward of hospital.wards) {
      const genderMatch = ward.gender_restriction === "No Restriction" || ward.gender_restriction === patient.gender;
      const ageMatch = patient.age >= ward.age_restriction[0] && patient.age <= ward.age_restriction[1];
      const specialRequirementsMatch = patient.special_requirements.every(req => ward.special_requirements.includes(req));

      if (genderMatch && ageMatch && specialRequirementsMatch) {
        for (const bed of ward.available_beds.sort((a, b) => a - b)) {
          assigned_hospital = hospital.id;
          assigned_ward = ward.ward_name;
          assigned_bed = bed;

          ward.available_beds = ward.available_beds.filter(b => b !== bed);

          return {
            patient_id: patient.id,
            assigned_hospital: assigned_hospital,
            assigned_ward: assigned_ward,
            assigned_bed: assigned_bed,
            reallocated_patients: reallocated_patients
          };
        }
      }
    }
  }

  // Reallocation (Second Attempt - only for high-risk patients)
  if (isHighRisk) {
    for (const hospital of hospitals) {
      if (hospital.model !== 4) continue;

      for (const ward of hospital.wards) {
        for (const currentPatient of ward.current_patients) {
          if (currentPatient.days_in_hospital > 3 && !currentPatient.non_transferable) {
            // Check if the current patient can be moved to a lower-level hospital
            for (const lowerHospital of hospitals) {
              if (lowerHospital.model >= 4) continue;

              for (const lowerWard of lowerHospital.wards) {
                const genderMatch = lowerWard.gender_restriction === "No Restriction" || lowerWard.gender_restriction === currentPatient.gender;
                const ageMatch = currentPatient.age >= lowerWard.age_restriction[0] && currentPatient.age <= lowerWard.age_restriction[1];
                const specialRequirementsMatch = currentPatient.special_requirements ? currentPatient.special_requirements.every(req => lowerWard.special_requirements.includes(req)) : true;

                if (genderMatch && ageMatch && specialRequirementsMatch && lowerWard.available_beds.length > 0) {
                  // Assign the high-risk patient to the bed of the transferable patient
                  assigned_hospital = hospital.id;
                  assigned_ward = ward.ward_name;
                  assigned_bed = currentPatient.bed_number;

                  // Move the existing patient to the lowest numbered available bed in their new ward
                  const newBed = lowerWard.available_beds.sort((a, b) => a - b)[0];
                  lowerWard.available_beds = lowerWard.available_beds.filter(b => b !== newBed);

                  reallocated_patients.push({
                    patient_id: currentPatient.id,
                    new_hospital: lowerHospital.id,
                    new_ward: lowerWard.ward_name,
                    new_bed: newBed
                  });

                  // Remove the reallocated patient from current_patients in original ward
                  ward.current_patients = ward.current_patients.filter(p => p.id !== currentPatient.id);

                  return {
                    patient_id: patient.id,
                    assigned_hospital: assigned_hospital,
                    assigned_ward: assigned_ward,
                    assigned_bed: assigned_bed,
                    reallocated_patients: reallocated_patients
                  };
                }
              }
            }
          }
        }
      }
    }
  }

  // No Assignment (Final Case)
  return {
    patient_id: patient.id,
    assigned_hospital: null,
    assigned_ward: null,
    assigned_bed: null,
    reallocated_patients: reallocated_patients
  };
}

if (typeof process !== 'undefined' && process.argv.length > 2) {
  let jsonString = '';
  process.stdin.on('data', (chunk) => {
    jsonString += chunk;
  });
  process.stdin.on('end', () => {
    try {
      const input = JSON.parse(jsonString);
      const result = reallocateBed(input.patient, input.hospitals);
      console.log(JSON.stringify(result));
    } catch (error) {
      console.error('Error parsing JSON input:', error);
    }
  });
}