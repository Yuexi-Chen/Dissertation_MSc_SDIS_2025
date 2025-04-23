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
      if (isMatchingWard(patient, ward)) {
        for (const bed of ward.available_beds) {
          result.assigned_hospital = hospital.id;
          result.assigned_ward = ward.ward_name;
          result.assigned_bed = bed;
          return result;
        }
      }
    }
  }

  // Reallocation for high-risk patients
  if (isHighRisk) {
    for (const hospital of hospitals.filter(h => h.model === 4)) {
      for (const ward of hospital.wards) {
        if (isMatchingWard(patient, ward)) {
          for (const currentPatient of ward.current_patients) {
            if (currentPatient.days_in_hospital > 3 && !currentPatient.non_transferable) {
              const newHospital = findLowerLevelHospital(currentPatient, hospitals);
              if (newHospital) {
                result.assigned_hospital = hospital.id;
                result.assigned_ward = ward.ward_name;
                result.assigned_bed = currentPatient.bed_number;
                result.reallocated_patients.push({
                  patient_id: currentPatient.id,
                  new_hospital: newHospital.id,
                  new_ward: newHospital.ward.ward_name,
                  new_bed: newHospital.ward.available_beds[0]
                });
                return result;
              }
            }
          }
        }
      }
    }
  }

  return result;
}

function isMatchingWard(patient, ward) {
  return (
    (ward.gender_restriction === "No Restriction" || ward.gender_restriction === `${patient.gender} Only`) &&
    patient.age >= ward.age_restriction[0] &&
    patient.age <= ward.age_restriction[1] &&
    patient.special_requirements.every(req => ward.special_requirements.includes(req))
  );
}

function findLowerLevelHospital(patient, hospitals) {
  for (const hospital of hospitals.filter(h => h.model < 4)) {
    for (const ward of hospital.wards) {
      if (isMatchingWard(patient, ward) && ward.available_beds.length > 0) {
        return { id: hospital.id, ward: ward };
      }
    }
  }
  return null;
}

let inputData = '';
rl.on('line', (line) => {
  inputData += line;
}).on('close', () => {
  const { patient, hospitals } = JSON.parse(inputData);
  const result = reallocateBed(patient, hospitals);
  console.log(JSON.stringify(result));
});