const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

function allocateBed(patient, wards) {
  for (const ward of wards) {
    if (matchWard(patient, ward)) {
      // Try regular beds
      if (ward.available_beds.length > 0) {
        return {
          patient_id: patient.id,
          assigned_ward: ward.ward_name,
          assigned_bed: Math.min(...ward.available_beds),
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

function matchWard(patient, ward) {
  return (
    patient.condition === ward.target_condition &&
    matchGender(patient.gender, ward.gender_restriction) &&
    patient.age >= ward.age_restriction[0] &&
    patient.age <= ward.age_restriction[1] &&
    patient.special_requirements.every(req => ward.special_requirements.includes(req))
  );
}

function matchGender(patientGender, wardRestriction) {
  if (wardRestriction === 'No Restriction' || wardRestriction === 'No Gender Restriction') {
    return true;
  }
  if (wardRestriction === 'Male Only' && patientGender === 'Male') {
    return true;
  }
  if (wardRestriction === 'Female Only' && patientGender === 'Female') {
    return true;
  }
  return false;
}

let inputData = '';
rl.on('line', (line) => {
  inputData += line;
});

rl.on('close', () => {
  const { patient, wards } = JSON.parse(inputData);
  const result = allocateBed(patient, wards);
  console.log(JSON.stringify(result));
});