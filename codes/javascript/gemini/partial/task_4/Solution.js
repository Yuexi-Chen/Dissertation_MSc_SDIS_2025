function allocateResources(patients, resources, responders, totalTime) {
    const numPatients = patients.length;
    const numResources = resources.length;

    let assignments = [];
    let patientProbabilities = patients.map(patient => [...patient]);

    let responderAvailability = Array(responders).fill(0); // Time when each responder is available

    let possibleAssignments = [];

    for (let patientIndex = 0; patientIndex < numPatients; patientIndex++) {
        for (let resourceIndex = 0; resourceIndex < numResources; resourceIndex++) {
            for (let time = 0; time < totalTime; time++) {
                if (time + resources[resourceIndex].time <= totalTime && time < patients[patientIndex].length) {
                    possibleAssignments.push({
                        patient: patientIndex,
                        resource: resourceIndex,
                        time: time
                    });
                }
            }
        }
    }

    possibleAssignments.sort((a, b) => {
        const probA = Math.min(100, patients[a.patient][a.time] + resources[a.resource].boost);
        const probB = Math.min(100, patients[b.patient][b.time] + resources[b.resource].boost);
        return probB - probA;
    });

    for (const assignment of possibleAssignments) {
        let bestResponder = -1;
        let earliestAvailability = Infinity;

        for (let i = 0; i < responders; i++) {
            if (responderAvailability[i] <= assignment.time && responderAvailability[i] < earliestAvailability) {
                earliestAvailability = responderAvailability[i];
                bestResponder = i;
            }
        }

        if (bestResponder !== -1) {
            assignments.push({
                patient: assignment.patient,
                resource: assignment.resource,
                time: assignment.time
            });

            responderAvailability[bestResponder] = assignment.time + resources[assignment.resource].time;

            patientProbabilities[assignment.patient] = patients[assignment.patient].map((prob, index) => {
                if (index >= assignment.time) {
                    if (index === assignment.time) {
                        return Math.min(100, prob + resources[assignment.resource].boost);
                    } else {
                        return prob;
                    }
                } else {
                    return prob;
                }
            });
        }
    }

    let survivors = 0;
    let totalSurvivalProbability = 0;

    for (let i = 0; i < numPatients; i++) {
        let finalProbability = patients[i][patients[i].length - 1];
        for(let assignment of assignments){
            if(assignment.patient === i){
                finalProbability = Math.min(100, patients[i][assignment.time] + resources[assignment.resource].boost);
            }
        }
        
        if (finalProbability > 50) {
            survivors++;
        }
        totalSurvivalProbability += finalProbability;
    }

    return {
        assignments: assignments,
        survivors: survivors,
        total_survival_probability: totalSurvivalProbability
    };
}