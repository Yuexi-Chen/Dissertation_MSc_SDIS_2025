const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

function reallocateBed(patient, hospitals) {
  const isHighRisk = patient.is_post_surgery;
  let result = {
    patient_id: patient.id,
    assigned_hospital: null,
    assigned_ward: null,
    assigned_bed: null,
    reallocated_patients: []
  };

  // Direct Assignment
  for (const hospital of hospitals) {
    if (isHighRisk && hospital.model !== 4) continue;
    if (!isHighRisk && hospital.model === 4) continue;

    for (const ward of hospital.wards) {
      if (isWardSuitable(patient, ward)) {
        const availableBed = ward.available_beds[0];
        if (availableBed) {
          result.assigned_hospital = hospital.id;
          result.assigned_ward = ward.ward_name;
          result.assigned_bed = availableBed;
          return result;
        }
      }
    }
  }

  // Reallocation for high-risk patients
  if (isHighRisk) {
    for (const hospital of hospitals.filter(h => h.model === 4)) {
      for (const ward of hospital.wards) {
        if (isWardSuitable(patient, ward)) {
          const transferablePatient = findTransferablePatient(ward, hospitals);
          if (transferablePatient) {
            result.assigned_hospital = hospital.id;
            result.assigned_ward = ward.ward_name;
            result.assigned_bed = transferablePatient.bed_number;
            result.reallocated_patients.push({
              patient_id: transferablePatient.id,
              new_hospital: transferablePatient.new_hospital,
              new_ward: transferablePatient.new_ward,
              new_bed: transferablePatient.new_bed
            });
            return result;
          }
        }
      }
    }
  }

  return result;
}

function isWardSuitable(patient, ward) {
  const genderMatch = ward.gender_restriction === 'No Restriction' ||
    (patient.gender === 'Male' && ward.gender_restriction === 'Male Only') ||
    (patient.gender === 'Female' && ward.gender_restriction === 'Female Only');
  
  const ageMatch = patient.age >= ward.age_restriction[0] && patient.age <= ward.age_restriction[1];
  
  const requirementsMatch = (patient.special_requirements || []).every(req => 
    ward.special_requirements.includes(req)
  );

  return genderMatch && ageMatch && requirementsMatch;
}

function findTransferablePatient(ward, hospitals) {
  const transferableCandidates = ward.current_patients
    .filter(p => p.days_in_hospital > 3 && !p.non_transferable)
    .sort((a, b) => b.days_in_hospital - a.days_in_hospital || a.bed_number - b.bed_number);

  for (const patient of transferableCandidates) {
    for (const hospital of hospitals.filter(h => h.model < 4)) {
      for (const newWard of hospital.wards) {
        if (isWardSuitable(patient, newWard) && newWard.available_beds.length > 0) {
          return {
            ...patient,
            new_hospital: hospital.id,
            new_ward: newWard.ward_name,
            new_bed: newWard.available_beds[0]
          };
        }
      }
    }
  }

  return null;
}

rl.on('line', (input) => {
  const { patient, hospitals } = JSON.parse(input);
  const result = reallocateBed(patient, hospitals);
  console.log(JSON.stringify(result));
  rl.close();
});