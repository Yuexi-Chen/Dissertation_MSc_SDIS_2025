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
  const input = JSON.parse(inputData);
  const result = allocateResources(input.patients, input.resources, input.responders, input.total_time);
  console.log(JSON.stringify(result));
});

function allocateResources(patients, resources, responders, totalTime) {
  const assignments = [];
  let survivors = 0;
  let totalSurvivalProbability = 0;

  const dp = new Array(totalTime + 1).fill(null).map(() => 
    new Array(responders + 1).fill(null).map(() => 
      new Array(patients.length).fill(0)
    )
  );

  const backtrack = new Array(totalTime + 1).fill(null).map(() => 
    new Array(responders + 1).fill(null).map(() => 
      new Array(patients.length).fill(null)
    )
  );

  for (let t = 0; t <= totalTime; t++) {
    for (let r = 0; r <= responders; r++) {
      for (let p = 0; p < patients.length; p++) {
        if (t === 0 || r === 0) {
          dp[t][r][p] = p === 0 ? patients[p][0] : dp[t][r][p-1];
          continue;
        }

        dp[t][r][p] = Math.max(
          p > 0 ? dp[t][r][p-1] : 0,
          dp[t][r-1][p]
        );

        for (let i = 0; i < resources.length; i++) {
          const resource = resources[i];
          if (t >= resource.time && p > 0) {
            const prevProb = dp[t-resource.time][r-1][p-1];
            const patientProb = patients[p][t-resource.time];
            const newProb = Math.min(100, patientProb + resource.boost);
            const totalProb = prevProb + newProb;

            if (totalProb > dp[t][r][p]) {
              dp[t][r][p] = totalProb;
              backtrack[t][r][p] = {patient: p, resource: i, time: t - resource.time};
            }
          }
        }
      }
    }
  }

  let t = totalTime;
  let r = responders;
  let p = patients.length - 1;

  while (t > 0 && r > 0 && p >= 0) {
    const assignment = backtrack[t][r][p];
    if (assignment) {
      assignments.unshift(assignment);
      t = assignment.time;
      r--;
      p--;
    } else {
      p--;
    }
  }

  const finalProbabilities = new Array(patients.length).fill(0);

  for (const assignment of assignments) {
    const { patient, resource, time } = assignment;
    const baseProb = patients[patient][time];
    finalProbabilities[patient] = Math.min(100, baseProb + resources[resource].boost);
  }

  for (let i = 0; i < patients.length; i++) {
    if (finalProbabilities[i] === 0) {
      finalProbabilities[i] = patients[i][totalTime];
    }
    if (finalProbabilities[i] > 50) {
      survivors++;
    }
    totalSurvivalProbability += finalProbabilities[i];
  }

  return {
    assignments,
    survivors,
    total_survival_probability: totalSurvivalProbability
  };
}