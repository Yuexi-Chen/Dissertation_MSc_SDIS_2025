function allocateResources(patients, resources, responders, totalTime) {
    let n = patients.length;
    let assignments = [];
    let maxSurvivors = 0;
    let maxSurvivalProbability = 0;

    function calculateSurvivalProbability(patientIndex, resource, time) {
        let baseProbability = patients[patientIndex][time];
        let boostedProbability = baseProbability + resource.boost;
        return Math.min(boostedProbability, 100);
    }

    let dp = Array.from({ length: totalTime + 1 }, () => Array.from({ length: responders + 1 }, () => ({ survivors: 0, survivalProbability: 0, path: [] })));

    for (let t = 0; t <= totalTime; t++) {
        for (let r = 1; r <= responders; r++) {
            for (let patientIndex = 0; patientIndex < n; patientIndex++) {
                for (let resourceIndex = 0; resourceIndex < resources.length; resourceIndex++) {
                    let resource = resources[resourceIndex];
                    if (t + resource.time <= totalTime) {
                        let nextTime = t + resource.time;
                        let survivalProbability = calculateSurvivalProbability(patientIndex, resource, t);
                        let potentialSurvivors = dp[t][r - 1].survivors + (survivalProbability > 50 ? 1 : 0);
                        let potentialSurvivalProbability = dp[t][r - 1].survivalProbability + survivalProbability;

                        if (potentialSurvivors > dp[nextTime][r].survivors || (potentialSurvivors === dp[nextTime][r].survivors && potentialSurvivalProbability > dp[nextTime][r].survivalProbability)) {
                            dp[nextTime][r].survivors = potentialSurvivors;
                            dp[nextTime][r].survivalProbability = potentialSurvivalProbability;
                            dp[nextTime][r].path = [...dp[t][r - 1].path, { patient: patientIndex, resource: resourceIndex, time: t }];
                        }
                    }
                }
            }
        }
    }

    for (let r = 1; r <= responders; r++) {
        if (dp[totalTime][r].survivors > maxSurvivors || (dp[totalTime][r].survivors === maxSurvivors && dp[totalTime][r].survivalProbability > maxSurvivalProbability)) {
            maxSurvivors = dp[totalTime][r].survivors;
            maxSurvivalProbability = dp[totalTime][r].survivalProbability;
            assignments = dp[totalTime][r].path;
        }
    }

    return {
        assignments: assignments,
        survivors: maxSurvivors,
        total_survival_probability: maxSurvivalProbability
    };
}

function main() {
    const fs = require('fs');
    const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
    const result = allocateResources(input.patients, input.resources, input.responders, input.total_time);
    console.log(JSON.stringify(result));
}

main();