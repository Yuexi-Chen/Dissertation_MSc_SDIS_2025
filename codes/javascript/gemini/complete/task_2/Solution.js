function reallocateBed(patient, hospitals) {
    const patient_id = patient.id;
    let assigned_hospital = null;
    let assigned_ward = null;
    let assigned_bed = null;
    const reallocated_patients = [];

    const isHighRisk = patient.is_post_surgery;

    const suitableHospitals = hospitals.filter(hospital => {
        if (isHighRisk) {
            return hospital.model === 4;
        } else {
            return true;
        }
    });

    for (const hospital of suitableHospitals) {
        for (const ward of hospital.wards) {
            if (
                (ward.gender_restriction === 'No Restriction' ||
                    (patient.gender === 'Female' && ward.gender_restriction === 'Female Only') ||
                    (patient.gender === 'Male' && ward.gender_restriction === 'Male Only')) &&
                patient.age >= ward.age_restriction[0] &&
                patient.age <= ward.age_restriction[1] &&
                patient.special_requirements.every(req => ward.special_requirements.includes(req))
            ) {
                if (ward.available_beds && ward.available_beds.length > 0) {
                    const bed = ward.available_beds.sort((a, b) => a - b)[0];
                    assigned_hospital = hospital.id;
                    assigned_ward = ward.ward_name;
                    assigned_bed = bed;
                    return {
                        patient_id,
                        assigned_hospital,
                        assigned_ward,
                        assigned_bed,
                        reallocated_patients,
                    };
                }
            }
        }
    }

    if (isHighRisk) {
        for (const hospital of hospitals) {
            if (hospital.model === 4) {
                for (const ward of hospital.wards) {
                    const transferablePatients = ward.current_patients
                        .filter(
                            p =>
                                p.days_in_hospital > 3 &&
                                !p.non_transferable
                        )
                        .sort((a, b) => {
                            if (b.days_in_hospital !== a.days_in_hospital) {
                                return b.days_in_hospital - a.days_in_hospital;
                            } else {
                                return a.bed_number - b.bed_number;
                            }
                        });

                    for (const transferablePatient of transferablePatients) {
                        for (const lowerLevelHospital of hospitals) {
                            if (lowerLevelHospital.model < 4) {
                                for (const lowerLevelWard of lowerLevelHospital.wards) {
                                    if (
                                        (lowerLevelWard.gender_restriction === 'No Restriction' ||
                                            (transferablePatient.gender === 'Female' &&
                                                lowerLevelWard.gender_restriction === 'Female Only') ||
                                            (transferablePatient.gender === 'Male' &&
                                                lowerLevelWard.gender_restriction === 'Male Only')) &&
                                        transferablePatient.age >= lowerLevelWard.age_restriction[0] &&
                                        transferablePatient.age <= lowerLevelWard.age_restriction[1] &&
                                        (transferablePatient.special_requirements || []).every(req =>
                                            lowerLevelWard.special_requirements.includes(req)
                                        )
                                    ) {
                                        if (lowerLevelWard.available_beds && lowerLevelWard.available_beds.length > 0) {
                                            const newBed = lowerLevelWard.available_beds.sort((a, b) => a - b)[0];

                                            assigned_hospital = hospital.id;
                                            assigned_ward = ward.ward_name;
                                            assigned_bed = transferablePatient.bed_number;

                                            reallocated_patients.push({
                                                patient_id: transferablePatient.id,
                                                new_hospital: lowerLevelHospital.id,
                                                new_ward: lowerLevelWard.ward_name,
                                                new_bed: newBed,
                                            });

                                            return {
                                                patient_id,
                                                assigned_hospital,
                                                assigned_ward,
                                                assigned_bed,
                                                reallocated_patients,
                                            };
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    return {
        patient_id: patient_id,
        assigned_hospital: assigned_hospital,
        assigned_ward: assigned_ward,
        assigned_bed: assigned_bed,
        reallocated_patients: reallocated_patients,
    };
}

if (typeof process !== 'undefined' && process.versions && process.versions.node) {
    process.stdin.setEncoding('utf8');

    let input = '';
    process.stdin.on('data', function (chunk) {
        input += chunk;
    });

    process.stdin.on('end', function () {
        try {
            const data = JSON.parse(input);
            const result = reallocateBed(data.patient, data.hospitals);
            console.log(JSON.stringify(result));
        } catch (e) {
            console.error(e);
        }
    });
}