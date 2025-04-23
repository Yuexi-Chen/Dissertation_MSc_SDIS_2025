const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

function dispatchAmbulance(emergency_event, ambulances, hospitals, regions) {
  // Construct graph
  const graph = constructGraph(regions);

  // Step 1: Select fastest ambulance
  const selectedAmbulance = selectFastestAmbulance(emergency_event, ambulances, graph);

  // Step 2: Select best hospital
  const selectedHospital = selectBestHospital(emergency_event, selectedAmbulance, hospitals, graph);

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
    for (const [destRegion, distance] of Object.entries(region.distances)) {
      if (!region.blocked_routes.includes(destRegion)) {
        const speed = getBaseSpeed(region.type);
        const travelTime = (distance / (speed * region.congestion_factor)) * 60;
        graph[region.region_id][destRegion] = Math.round(travelTime);
      }
    }
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

function selectFastestAmbulance(emergency, ambulances, graph) {
  const availableAmbulances = ambulances.filter(a => a.status === 'Available');
  if (emergency.severity === 'Critical' && !emergency.special_requirements.includes('Advanced Life Support')) {
    emergency.special_requirements.push('Advanced Life Support');
  }

  const suitableAmbulances = availableAmbulances.filter(a => 
    emergency.special_requirements.every(req => a.capabilities.includes(req))
  );

  if (suitableAmbulances.length === 0) return null;

  suitableAmbulances.sort((a, b) => {
    const timeA = dijkstra(graph, a.current_region, emergency.region_id);
    const timeB = dijkstra(graph, b.current_region, emergency.region_id);
    if (timeA !== timeB) return timeA - timeB;
    return a.capabilities.length > b.capabilities.length ? -1 : 1;
  });

  return suitableAmbulances[0];
}

function selectBestHospital(emergency, ambulance, hospitals, graph) {
  if (!ambulance) return null;

  const suitableHospitals = hospitals.filter(h => {
    if (emergency.severity === 'Critical') {
      return true;
    }
    return emergency.type === 'Cardiac' ? h.capabilities.includes('Cardiac Center') :
           emergency.type === 'Trauma' ? h.capabilities.includes('Trauma Center') :
           emergency.type === 'Stroke' ? h.capabilities.includes('Stroke Unit') : true;
  });

  if (suitableHospitals.length === 0) return null;

  suitableHospitals.sort((a, b) => {
    const timeA = dijkstra(graph, emergency.region_id, a.region_id);
    const timeB = dijkstra(graph, emergency.region_id, b.region_id);
    if (timeA !== timeB) return timeA - timeB;
    return getEmergencyCapacityScore(b.emergency_capacity) - getEmergencyCapacityScore(a.emergency_capacity);
  });

  return suitableHospitals[0];
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

  while (visited.size !== nodes.length) {
    const current = nodes
      .filter(node => !visited.has(node))
      .reduce((closest, node) => distances[node] < distances[closest] ? node : closest);

    if (current === end) break;

    visited.add(current);

    for (const [neighbor, time] of Object.entries(graph[current])) {
      const distance = distances[current] + time;
      if (distance < distances[neighbor]) {
        distances[neighbor] = distance;
      }
    }
  }

  return Math.round(distances[end]);
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