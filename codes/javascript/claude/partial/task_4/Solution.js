function allocateResources(patients, resources, responders, totalTime) {
    const assignments = [];
    let survivors = 0;
    let totalSurvivalProbability = 0;

    // Helper function to calculate probability after treatment
    function calculateProbability(patientProb, resourceBoost, time) {
        return Math.min(100, patientProb[time] + resourceBoost);
    }

    // Dynamic programming approach
    const dp = new Array(totalTime + 1).fill(0).map(() => new Array(responders + 1).fill(0));
    const decisions = new Array(totalTime + 1).fill(0).map(() => new Array(responders + 1).fill(null));

    for (let t = 0; t <= totalTime; t++) {
        for (let r = 0; r <= responders; r++) {
            for (let p = 0; p < patients.length; p++) {
                for (let res = 0; res < resources.length; res++) {
                    if (t + resources[res].time <= totalTime && r > 0) {
                        const probBefore = patients[p][t] || 0;
                        const probAfter = calculateProbability(patients[p], resources[res].boost, t + resources[res].time);
                        const gain = probAfter - probBefore;

                        if (gain > 0) {
                            const newValue = dp[t][r - 1] + gain;
                            if (newValue > dp[t + resources[res].time][r]) {
                                dp[t + resources[res].time][r] = newValue;
                                decisions[t + resources[res].time][r] = { patient: p, resource: res, time: t };
                            }
                        }
                    }
                }
            }
        }
    }

    // Backtrack to find assignments
    let t = totalTime;
    let r = responders;
    while (t > 0 && r > 0) {
        const decision = decisions[t][r];
        if (decision) {
            assignments.push(decision);
            t -= resources[decision.resource].time;
            r--;
        } else {
            t--;
        }
    }

    // Calculate final probabilities and statistics
    const finalProbs = patients.map(p => p[0]);
    for (const { patient, resource, time } of assignments) {
        finalProbs[patient] = calculateProbability(patients[patient], resources[resource].boost, time + resources[resource].time);
    }

    survivors = finalProbs.filter(p => p > 50).length;
    totalSurvivalProbability = finalProbs.reduce((sum, p) => sum + p, 0);

    return { assignments, survivors, total_survival_probability: totalSurvivalProbability };
}

// Read input from stdin
const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

let inputData = '';

rl.on('line', (line) => {
    inputData += line;
});

rl.on('close', () => {
    const { patients, resources, responders, total_time } = JSON.parse(inputData);
    const result = allocateResources(patients, resources, responders, total_time);
    console.log(JSON.stringify(result));
});