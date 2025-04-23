function allocateResources(patients, resources, responders, totalTime) {
  const assignments = [];
  let survivors = 0;
  let total_survival_probability = 0;

  if (!patients || patients.length === 0 || !resources || resources.length === 0 || !responders || responders <= 0 || !totalTime || totalTime <= 0) {
    return { assignments: [], survivors: 0, total_survival_probability: 0 };
  }

  const patientCount = patients.length;
  const resourceCount = resources.length;

  const possibleAssignments = [];

  for (let i = 0; i < patientCount; i++) {
    for (let j = 0; j < resourceCount; j++) {
      for (let t = 0; t <= totalTime - resources[j].time; t++) {
        const baseProbability = patients[i][t];
        const boostedProbability = Math.min(100, baseProbability + resources[j].boost);

        let finalProbability = boostedProbability;
        
        possibleAssignments.push({
          patient: i,
          resource: j,
          time: t,
          probability: finalProbability / 100, 
        });
      }
    }
  }
  
  possibleAssignments.sort((a, b) => b.probability - a.probability);

  const responderAvailability = new Array(responders).fill(0);
  const assignedPatients = new Set();

  for (const assignment of possibleAssignments) {
    const patient = assignment.patient;
    const resource = assignment.resource;
    const time = assignment.time;
    const probability = assignment.probability;

    if (assignedPatients.has(patient)) {
      continue;
    }

    let availableResponderIndex = -1;
    for (let i = 0; i < responders; i++) {
      if (responderAvailability[i] <= time) {
        availableResponderIndex = i;
        break;
      }
    }

    if (availableResponderIndex !== -1) {
      assignments.push({
        patient: patient,
        resource: resource,
        time: time,
      });
      responderAvailability[availableResponderIndex] = time + resources[resource].time;
      assignedPatients.add(patient);
    }
  }

  for (let i = 0; i < patients.length; i++) {
    let survivalProbability = 0;
    let assignedTime = -1;
    let assignedResourceIndex = -1;

    for (const assignment of assignments) {
      if (assignment.patient === i) {
        assignedTime = assignment.time;
        assignedResourceIndex = assignment.resource;
        break;
      }
    }

    if (assignedTime !== -1) {
        const baseProbability = patients[i][assignedTime];
        survivalProbability = Math.min(100, baseProbability + resources[assignedResourceIndex].boost);
        survivors++;
        total_survival_probability += survivalProbability;
      
    }
  }

  return {
    assignments: assignments,
    survivors: survivors,
    total_survival_probability: total_survival_probability,
  };
}

if (typeof process !== 'undefined' && process.argv) {
  let inputData = '';

  process.stdin.on('data', (chunk) => {
    inputData += chunk;
  });

  process.stdin.on('end', () => {
    try {
      const parsedInput = JSON.parse(inputData);
      const result = allocateResources(parsedInput.patients, parsedInput.resources, parsedInput.responders, parsedInput.total_time);
      console.log(JSON.stringify(result));
    } catch (error) {
      console.error('Error parsing JSON input:', error);
      console.error('Input data:', inputData);
    }
  });
}