function allocateResources(patients, resources, responders, totalTime) {
    // Step 1: Initialize variables
    let assignments = [];
    let availability = Array(responders).fill(0); // Track responder availability
    let total_survival_probability = 0;
    let survivors = 0;

    // Step 2: Helper function to calculate final probability after treatment
    function calculateFinalProbability(patient, startTime, resource) {
        let initialProb = patient[startTime] || 0;
        let finalProb = initialProb + resource.boost;
        return Math.min(finalProb, 100); // Probabilities cannot exceed 100%
    }

    // Step 3: Allocate resources
    for (let time = 0; time < totalTime; time++) {
        for (let patientIndex = 0; patientIndex < patients.length; patientIndex++) {
            let bestResource = null;
            let bestProbIncrease = 0;
            let startTime = -1;

            // Find the best resource for the current patient at the current time
            for (let resourceIndex = 0; resourceIndex < resources.length; resourceIndex++) {
                const resource = resources[resourceIndex];
                const treatmentTime = time + resource.time;

                if (treatmentTime <= totalTime && availability.includes(time)) {
                    const finalProb = calculateFinalProbability(patients[patientIndex], time, resource);
                    const probIncrease = finalProb - patients[patientIndex][time];

                    // Choose the resource that provides the highest probability increase
                    if (probIncrease > bestProbIncrease) {
                        bestProbIncrease = probIncrease;
                        bestResource = resourceIndex;
                        startTime = time;
                    }
                }
            }

            // Step 4: Assign the best resource if available
            if (bestResource !== null) {
                const responderIndex = availability.indexOf(time);
                availability[responderIndex] = time + resources[bestResource].time; // Update responder availability
                assignments.push({ patient: patientIndex, resource: bestResource, time: startTime });

                const finalProb = calculateFinalProbability(patients[patientIndex], startTime, resources[bestResource]);
                patients[patientIndex][startTime] = finalProb;

                // Update total survival probability
                total_survival_probability += finalProb;
            }
        }
    }

    // Step 5: Calculate survivors
    for (let patient of patients) {
        const finalProb = Math.max(...patient);
        if (finalProb > 50) {
            survivors++;
        }
    }

    // Step 6: Return the result
    return {
        assignments,
        survivors,
        total_survival_probability
    };
}

// Reading input from stdin
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const result = allocateResources(input.patients, input.resources, input.responders, input.total_time);

// Print result as JSON
console.log(JSON.stringify(result));