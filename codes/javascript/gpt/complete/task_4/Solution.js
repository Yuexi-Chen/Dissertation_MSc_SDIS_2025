function allocateResources(patients, resources, responders, totalTime) {
    const assignments = [];
    const numPatients = patients.length;
    const numResources = resources.length;
    let availableResponders = Array(totalTime).fill(responders);
    let finalProbabilities = Array(numPatients).fill(0);

    // Helper function to get probability at a specific time
    function getProbability(patientIndex, time) {
        if (time < patients[patientIndex].length) {
            return patients[patientIndex][time];
        }
        return 0;
    }

    // Try to allocate resources optimally
    for (let time = 0; time < totalTime; time++) {
        for (let r = 0; r < numResources; r++) {
            if (resources[r].time > totalTime - time) continue;
            const endTime = time + resources[r].time;
            if (availableResponders[time] > 0) {
                let bestPatient = -1;
                let bestBoost = -1;

                for (let p = 0; p < numPatients; p++) {
                    const currentProbability = getProbability(p, time);
                    const boostedProbability = currentProbability + resources[r].boost;
                    if (boostedProbability > 100) boostedProbability = 100;

                    if (boostedProbability > currentProbability && boostedProbability > bestBoost) {
                        bestBoost = boostedProbability;
                        bestPatient = p;
                    }
                }

                if (bestPatient !== -1) {
                    assignments.push({ patient: bestPatient, resource: r, time: time });
                    finalProbabilities[bestPatient] = bestBoost;
                    for (let t = time; t < endTime; t++) {
                        availableResponders[t]--;
                    }
                }
            }
        }
    }

    // Calculate survivors and total survival probability
    let survivors = 0;
    let totalSurvivalProbability = 0;
    for (let p = 0; p < numPatients; p++) {
        totalSurvivalProbability += finalProbabilities[p];
        if (finalProbabilities[p] > 50) {
            survivors++;
        }
    }

    return {
        assignments,
        survivors,
        total_survival_probability: totalSurvivalProbability
    };
}

// Read input from stdin, parse it as JSON, and call allocateResources
const fs = require('fs');
const input = fs.readFileSync('/dev/stdin', 'utf8');
const data = JSON.parse(input);
const result = allocateResources(data.patients, data.resources, data.responders, data.total_time);
console.log(JSON.stringify(result));