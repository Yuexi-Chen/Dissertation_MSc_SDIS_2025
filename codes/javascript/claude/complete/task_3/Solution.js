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
  const result = dispatchAmbulance(input.emergency_event, input.ambulances, input.hospitals, input.regions);
  console.log(JSON.stringify(result));
});

function dispatchAmbulance(emergency_event, ambulances, hospitals, regions) {
  const graph = buildGraph(regions);
  const suitableAmbulance = selectAmbulance(emergency_event, ambulances, graph);
  
  if (!suitableAmbulance) {
    return { emergency_id: emergency_event.id, assigned_ambulance: null, destination_hospital: null };
  }
  
  const suitableHospital = selectHospital(emergency_event, suitableAmbulance, hospitals, graph);
  
  return {
    emergency_id: emergency_event.id,
    assigned_ambulance: suitableAmbulance.id,
    destination_hospital: suitableHospital ? suitableHospital.id : null
  };
}

function buildGraph(regions) {
  const graph = {};
  
  regions.forEach(region => {
    graph[region.region_id] = {};
    Object.entries(region.distances).forEach(([neighborId, distance]) => {
      if (!region.blocked_routes.includes(neighborId)) {
        const neighborRegion = regions.find(r => r.region_id === neighborId);
        const travelTime = calculateTravelTime(distance, region, neighborRegion);
        graph[region.region_id][neighborId] = travelTime;
      }
    });
  });
  
  return graph;
}

function calculateTravelTime(distance, fromRegion, toRegion) {
  const speed = Math.min(fromRegion.speed, toRegion.speed);
  const congestionFactor = Math.min(fromRegion.congestion_factor, toRegion.congestion_factor);
  return Math.round((distance / (speed * congestionFactor)) * 60);
}

function selectAmbulance(emergency, ambulances, graph) {
  const suitableAmbulances = ambulances.filter(ambulance => 
    ambulance.status === 'Available' &&
    (emergency.severity !== 'Critical' || ambulance.capabilities.includes('Advanced Life Support')) &&
    emergency.special_requirements.every(req => ambulance.capabilities.includes(req))
  );
  
  if (suitableAmbulances.length === 0) return null;
  
  suitableAmbulances.forEach(ambulance => {
    ambulance.arrivalTime = dijkstra(graph, ambulance.current_region, emergency.region_id);
  });
  
  suitableAmbulances.sort((a, b) => {
    if (a.arrivalTime !== b.arrivalTime) return a.arrivalTime - b.arrivalTime;
    if (a.capabilities.length !== b.capabilities.length) return b.capabilities.length - a.capabilities.length;
    return a.id.localeCompare(b.id);
  });
  
  return suitableAmbulances[0];
}

function selectHospital(emergency, ambulance, hospitals, graph) {
  const suitableHospitals = hospitals.filter(hospital => 
    emergency.severity !== 'Critical' ? 
      hospital.capabilities.includes(`${emergency.type} Center`) :
      hospital.capabilities.some(cap => cap.includes('Emergency') || cap.includes(emergency.type))
  );
  
  if (suitableHospitals.length === 0) {
    return hospitals.find(h => h.capabilities.some(cap => cap.includes('Emergency')));
  }
  
  suitableHospitals.forEach(hospital => {
    hospital.arrivalTime = dijkstra(graph, emergency.region_id, hospital.region_id);
  });
  
  suitableHospitals.sort((a, b) => {
    if (a.emergency_capacity !== b.emergency_capacity) {
      return ['High', 'Medium', 'Low'].indexOf(a.emergency_capacity) - 
             ['High', 'Medium', 'Low'].indexOf(b.emergency_capacity);
    }
    return a.arrivalTime - b.arrivalTime;
  });
  
  return suitableHospitals[0];
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
      .reduce((min, node) => distances[node] < distances[min] ? node : min);
    
    if (current === end) break;
    
    visited.add(current);
    
    Object.entries(graph[current]).forEach(([neighbor, time]) => {
      const alt = distances[current] + time;
      if (alt < distances[neighbor]) {
        distances[neighbor] = alt;
      }
    });
  }
  
  return Math.round(distances[end]);
}