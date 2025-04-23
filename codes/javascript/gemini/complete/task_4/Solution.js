function allocateResources(patients, resources, responders, totalTime) {
  const numPatients = patients.length;
  const numResources = resources.length;

  let assignments = [];
  let total_survival_probability = 0;
  let survivors = 0;

  let patientProbabilities = patients.map(patient => [...patient]);
  let responderAvailability = Array(totalTime).fill(0);

  function calculateFinalProbability(patientIndex, resourceIndex, time) {
    let initialProbability = patientProbabilities[patientIndex][time];
    let boostedProbability = initialProbability + resources[resourceIndex].boost;
    return Math.min(boostedProbability, 100);
  }

  function findBestAssignment() {
    let bestAssignment = null;
    let maxTotalProbability = -1;

    for (let patientIndex = 0; patientIndex < numPatients; patientIndex++) {
      for (let resourceIndex = 0; resourceIndex < numResources; resourceIndex++) {
        for (let time = 0; time < totalTime; time++) {
          if (time + resources[resourceIndex].time <= totalTime && patientProbabilities[patientIndex][time] > 0) {
            let availableResponders = 0;
            for(let t = time; t < time + resources[resourceIndex].time; t++){
              availableResponders += responderAvailability[t];
            }
            if(availableResponders < responders){
              let finalProbability = calculateFinalProbability(patientIndex, resourceIndex, time);
              let tempPatientsProbabilities = patientProbabilities.map(patient => [...patient]);
              
              tempPatientsProbabilities[patientIndex][0] = finalProbability;

              let currentTotalProbability = 0;
              for(let i = 0; i < numPatients; i++){
                currentTotalProbability += tempPatientsProbabilities[i][0];
              }

              if (currentTotalProbability > maxTotalProbability) {
                maxTotalProbability = currentTotalProbability;
                bestAssignment = {
                  patient: patientIndex,
                  resource: resourceIndex,
                  time: time,
                  finalProbability: finalProbability
                };
              }
            }
          }
        }
      }
    }
    return bestAssignment;
  }

  while (true) {
    let bestAssignment = findBestAssignment();

    if (!bestAssignment) {
      break;
    }

    assignments.push({
      patient: bestAssignment.patient,
      resource: bestAssignment.resource,
      time: bestAssignment.time
    });
    
    patientProbabilities[bestAssignment.patient][0] = bestAssignment.finalProbability;
    
    for(let t = bestAssignment.time; t < bestAssignment.time + resources[bestAssignment.resource].time; t++){
      responderAvailability[t]++;
    }
  }

  for (let i = 0; i < numPatients; i++) {
    let finalProbability = patientProbabilities[i][0];
    if(finalProbability == undefined){
      finalProbability = patients[i][patients[i].length -1];
    }
    total_survival_probability += finalProbability;
    if (finalProbability > 50) {
      survivors++;
    }
  }

  return {
    assignments: assignments,
    survivors: survivors,
    total_survival_probability: total_survival_probability
  };
}

process.stdin.setEncoding('utf8');

let input = '';

process.stdin.on('data', function(chunk) {
  input += chunk;
});

process.stdin.on('end', function() {
  try {
    const data = JSON.parse(input);
    const result = allocateResources(data.patients, data.resources, data.responders, data.total_time);
    console.log(JSON.stringify(result));
  } catch (error) {
    console.error("Error processing input:", error);
  }
});