const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

function dispatchAmbulance(emergency_event, ambulances, hospitals, regions) {
  // Construct graph
  const graph = constructGraph(regions);

  // Step 1: Select fastest suitable ambulance
  const selectedAmbulance = selectAmbulance(emergency_event, ambulances, graph);

  // Step 2: Choose best hospital
  const selectedHospital = selectHospital(emergency_event, selectedAmbulance, hospitals, graph);

  return {
    emergency_id: emergency_event.id,
    assigned_ambulance: selectedAmbulance ? selectedAmbulance.id : null,
    destination_hospital: selectedHospital ? selectedHospital.id : null
  };
}

function constructGraph(regions) {
  const graph = {};
  regions.forEach(region => {
    graph[region.region_id] = {};
    Object.entries(region.distances).forEach(([neighbor, distance]) => {
      if (!region.blocked_routes.includes(neighbor)) {
        const speed = getBaseSpeed(region.type);
        const travelTime = (distance / (speed * region.congestion_factor)) * 60;
        graph[region.region_id][neighbor] = travelTime;
      }
    });
  });
  return graph;
}

function getBaseSpeed(regionType) {
  switch (regionType) {
    case 'Urban': return 30;
    case 'Suburban': return 50;
    case 'Rural': return 80;
    default: return 50;
  }
}

function selectAmbulance(emergency, ambulances, graph) {
  const suitableAmbulances = ambulances.filter(a => 
    a.status === 'Available' &&
    (emergency.severity !== 'Critical' || a.capabilities.includes('Advanced Life Support'))
  );

  let fastestAmbulance = null;
  let shortestTime = Infinity;

  suitableAmbulances.forEach(ambulance => {
    const time = dijkstra(graph, ambulance.current_region, emergency.region_id);
    if (time < shortestTime || 
        (time === shortestTime && 
         ambulance.capabilities.length > fastestAmbulance.capabilities.length) ||
        (time === shortestTime && 
         ambulance.capabilities.length === fastestAmbulance.capabilities.length &&
         ambulance.id < fastestAmbulance.id)) {
      shortestTime = time;
      fastestAmbulance = ambulance;
    }
  });

  return fastestAmbulance;
}

function selectHospital(emergency, ambulance, hospitals, graph) {
  if (!ambulance) return null;

  const suitableHospitals = hospitals.filter(h => 
    emergency.severity === 'Critical' || 
    h.capabilities.includes(emergency.type + ' Center')
  );

  let bestHospital = null;
  let shortestTime = Infinity;

  suitableHospitals.forEach(hospital => {
    const time = dijkstra(graph, ambulance.current_region, hospital.region_id);
    if (time < shortestTime || 
        (time === shortestTime && 
         getEmergencyCapacityScore(hospital.emergency_capacity) > 
         getEmergencyCapacityScore(bestHospital.emergency_capacity))) {
      shortestTime = time;
      bestHospital = hospital;
    }
  });

  return bestHospital;
}

function getEmergencyCapacityScore(capacity) {
  switch (capacity) {
    case 'High': return 3;
    case 'Medium': return 2;
    case 'Low': return 1;
    default: return 0;
  }
}

function dijkstra(graph, start, end) {
  const distances = {};
  const visited = new Set();
  const nodes = Object.keys(graph);

  nodes.forEach(node => {
    distances[node] = Infinity;
  });
  distances[start] = 0;

  while (visited.size < nodes.length) {
    const current = nodes
      .filter(node => !visited.has(node))
      .reduce((minNode, node) => 
        distances[node] < distances[minNode] ? node : minNode
      );

    if (current === end) return distances[end];

    visited.add(current);

    Object.entries(graph[current]).forEach(([neighbor, time]) => {
      const newDistance = distances[current] + time;
      if (newDistance < distances[neighbor]) {
        distances[neighbor] = newDistance;
      }
    });
  }

  return Infinity;
}

let inputData = '';
rl.on('line', (line) => {
  inputData += line;
});

rl.on('close', () => {
  const input = JSON.parse(inputData);
  const result = dispatchAmbulance(input.emergency_event, input.ambulances, input.hospitals, input.regions);
  console.log(JSON.stringify(result));
});