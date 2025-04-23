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
  const n = patients.length;
  const m = resources.length;
  
  const dp = Array(totalTime + 1).fill().map(() => Array(responders + 1).fill(0));
  const assignments = [];
  
  for (let t = 0; t <= totalTime; t++) {
    for (let r = 0; r <= responders; r++) {
      for (let i = 0; i < n; i++) {
        for (let j = 0; j < m; j++) {
          const resource = resources[j];
          if (t >= resource.time && r > 0) {
            const survivalProb = patients[i][t] + resource.boost;
            const newValue = dp[t - resource.time][r - 1] + survivalProb;
            if (newValue > dp[t][r]) {
              dp[t][r] = newValue;
              assignments.push({ patient: i, resource: j, time: t - resource.time });
            }
          }
        }
      }
    }
  }
  
  const survivors = Math.floor(dp[totalTime][responders] / 100);
  const totalSurvivalProbability = dp[totalTime][responders];
  
  return {
    assignments: assignments.slice(-survivors),
    survivors: survivors,
    total_survival_probability: totalSurvivalProbability
  };
}