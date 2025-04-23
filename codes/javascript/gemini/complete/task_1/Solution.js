function allocateBed(patient, wards) {
    let result = {
        patient_id: patient.id,
        assigned_ward: null,
        assigned_bed: null,
        assigned_satellite_hospital: null
    };

    for (let ward of wards) {
        // Ward Matching
        if (ward.target_condition !== patient.condition) {
            continue;
        }

        let genderRestriction = ward.gender_restriction;
        if (genderRestriction !== "No Restriction" && genderRestriction !== "No Gender Restriction") {
            if (genderRestriction === "Male Only" && patient.gender !== "Male") {
                continue;
            }
            if (genderRestriction === "Female Only" && patient.gender !== "Female") {
                continue;
            }
        }

        let ageRestriction = ward.age_restriction;
        if (patient.age < ageRestriction[0] || patient.age > ageRestriction[1]) {
            continue;
        }

        let wardRequirements = ward.special_requirements || [];
        let patientRequirements = patient.special_requirements || [];

        let requirementsMet = true;
        for (let requirement of patientRequirements) {
            if (!wardRequirements.includes(requirement)) {
                requirementsMet = false;
                break;
            }
        }
        if (!requirementsMet) {
            continue;
        }

        // Bed Allocation
        // Step 1: Regular Beds
        if (ward.available_beds && ward.available_beds.length > 0) {
            ward.available_beds.sort((a, b) => a - b);
            result.assigned_ward = ward.ward_name;
            result.assigned_bed = ward.available_beds.shift();
            return result;
        }

        // Step 2: Overflow Beds
        if (ward.overflow_capacity > 0) {
            let overflowBedsUsed = 0;
            if (ward.hasOwnProperty("_overflowBedsUsed")) {
                overflowBedsUsed = ward._overflowBedsUsed;
            } else {
                ward._overflowBedsUsed = 0;
            }
            
            if (overflowBedsUsed < ward.overflow_capacity) {
                ward._overflowBedsUsed++;
                result.assigned_ward = ward.ward_name;
                result.assigned_bed = "Overflow-" + ward._overflowBedsUsed;
                return result;
            }
            
        }

        // Step 3: Satellite Hospitals
        if (ward.satellite_hospitals && ward.satellite_hospitals.length > 0) {
            result.assigned_satellite_hospital = ward.satellite_hospitals[0];
            result.assigned_ward = null;
            result.assigned_bed = null;
            return result;
        }
    }

    return result;
}

if (typeof process !== 'undefined' && process.versions && process.versions.node) {
    process.stdin.setEncoding("utf8");
    let input = "";

    process.stdin.on("data", function (chunk) {
        input += chunk;
    });

    process.stdin.on("end", function () {
        try {
            const parsedInput = JSON.parse(input);
            const patient = parsedInput.patient;
            const wards = parsedInput.wards;
            const result = allocateBed(patient, wards);
            console.log(JSON.stringify(result));
        } catch (e) {
            console.error("Error parsing JSON input:", e);
        }
    });
}