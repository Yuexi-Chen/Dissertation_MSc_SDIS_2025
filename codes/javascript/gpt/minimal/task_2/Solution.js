function reallocateBed(patient, hospitals) {
    let isHighRisk = patient.is_post_surgery;
    let assignedHospital = null;
    let assignedWard = null;
    let assignedBed = null;
    let reallocatedPatients = [];

    function canPatientBeTransferred(existingPatient, ward) {
        return existingPatient.gender === ward.gender_restriction || ward.gender_restriction === "No Restriction"
            && existingPatient.age >= ward.age_restriction[0] && existingPatient.age <= ward.age_restriction[1]
            && ward.special_requirements.every(req => existingPatient.special_requirements.includes(req));
    }

    if (isHighRisk) {
        hospitals = hospitals.filter(h => h.model === 4);

        for (let hospital of hospitals) {
            for (let ward of hospital.wards) {
                if (ward.gender_restriction !== patient.gender && ward.gender_restriction !== "No Restriction") continue;
                if (patient.age < ward.age_restriction[0] || patient.age > ward.age_restriction[1]) continue;
                if (!ward.special_requirements.every(req => patient.special_requirements.includes(req))) continue;

                let availableBed = ward.available_beds.sort((a, b) => a - b).find(bed => true);
                if (availableBed !== undefined) {
                    assignedHospital = hospital.id;
                    assignedWard = ward.ward_name;
                    assignedBed = availableBed;
                    return {
                        patient_id: patient.id,
                        assigned_hospital: assignedHospital,
                        assigned_ward: assignedWard,
                        assigned_bed: assignedBed,
                        reallocated_patients: reallocatedPatients
                    };
                }

                for (let currentPatient of ward.current_patients) {
                    if (currentPatient.days_in_hospital > 3 && !currentPatient.non_transferable) {
                        for (let lowerHospital of hospitals.filter(h => h.model < 4)) {
                            for (let lowerWard of lowerHospital.wards) {
                                if (canPatientBeTransferred(currentPatient, lowerWard)) {
                                    let lowerBed = lowerWard.available_beds.sort((a, b) => a - b).find(bed => true);
                                    if (lowerBed !== undefined) {
                                        assignedHospital = hospital.id;
                                        assignedWard = ward.ward_name;
                                        assignedBed = currentPatient.bed_number;
                                        reallocatedPatients.push({
                                            patient_id: currentPatient.id,
                                            new_hospital: lowerHospital.id,
                                            new_ward: lowerWard.ward_name,
                                            new_bed: lowerBed
                                        });
                                        return {
                                            patient_id: patient.id,
                                            assigned_hospital: assignedHospital,
                                            assigned_ward: assignedWard,
                                            assigned_bed: assignedBed,
                                            reallocated_patients: reallocatedPatients
                                        };
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    } else {
        hospitals = hospitals.filter(h => h.model < 4);

        for (let hospital of hospitals) {
            for (let ward of hospital.wards) {
                if (ward.gender_restriction !== patient.gender && ward.gender_restriction !== "No Restriction") continue;
                if (patient.age < ward.age_restriction[0] || patient.age > ward.age_restriction[1]) continue;
                if (!ward.special_requirements.every(req => patient.special_requirements.includes(req))) continue;

                let availableBed = ward.available_beds.sort((a, b) => a - b).find(bed => true);
                if (availableBed !== undefined) {
                    assignedHospital = hospital.id;
                    assignedWard = ward.ward_name;
                    assignedBed = availableBed;
                    return {
                        patient_id: patient.id,
                        assigned_hospital: assignedHospital,
                        assigned_ward: assignedWard,
                        assigned_bed: assignedBed,
                        reallocated_patients: reallocatedPatients
                    };
                }
            }
        }
    }

    return {
        patient_id: patient.id,
        assigned_hospital: assignedHospital,
        assigned_ward: assignedWard,
        assigned_bed: assignedBed,
        reallocated_patients: reallocatedPatients
    };
}

const input = JSON.parse(require('fs').readFileSync(0, 'utf-8'));
const result = reallocateBed(input.patient, input.hospitals);
console.log(JSON.stringify(result));