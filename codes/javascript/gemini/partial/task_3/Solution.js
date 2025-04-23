const readline = require('readline');

function dispatchAmbulance(emergency_event, ambulances, hospitals, regions) {
    // 1. Input Validation and Default Initialization
    if (!emergency_event || !ambulances || !hospitals || !regions) {
        console.error("Invalid input: Missing required data.");
        return {
            emergency_id: emergency_event ? emergency_event.id : null,
            assigned_ambulance: null,
            destination_hospital: null
        };
    }

    const emergencyId = emergency_event.id;
    let assignedAmbulance = null;
    let destinationHospital = null;

    // 2. Graph Construction and Helper Functions
    function buildGraph(regions) {
        const graph = {};
        regions.forEach(region => {
            graph[region.region_id] = {};
            for (const neighbor in region.distances) {
                if (region.distances.hasOwnProperty(neighbor)) {
                    const distance = region.distances[neighbor];
                    const baseSpeed = region.type === "Urban" ? 30 : region.type === "Suburban" ? 50 : 80;
                    const congestionFactor = region.congestion_factor;
                    const travelTime = distance / (baseSpeed * congestionFactor) * 60;
                    graph[region.region_id][neighbor] = travelTime;
                }
            }
            region.blocked_routes.forEach(blockedRoute => {
                delete graph[region.region_id][blockedRoute];
            });
        });
        return graph;
    }

    function dijkstra(graph, startNode, endNode) {
        const distances = {};
        const visited = {};
        const previous = {};
        for (const node in graph) {
            distances[node] = Infinity;
            visited[node] = false;
        }
        distances[startNode] = 0;

        let currentNode = startNode;
        while (currentNode) {
            visited[currentNode] = true;

            for (const neighbor in graph[currentNode]) {
                if (graph[currentNode].hasOwnProperty(neighbor)) {
                    const travelTime = graph[currentNode][neighbor];
                    const newDistance = distances[currentNode] + travelTime;
                    if (newDistance < distances[neighbor]) {
                        distances[neighbor] = newDistance;
                        previous[neighbor] = currentNode;
                    }
                }
            }

            currentNode = null;
            let shortestDistance = Infinity;
            for (const node in distances) {
                if (!visited[node] && distances[node] < shortestDistance) {
                    shortestDistance = distances[node];
                    currentNode = node;
                }
            }
        }

        if (distances[endNode] === Infinity) {
            return { distance: Infinity, path: [] };
        }

        const path = [];
        let node = endNode;
        while (node) {
            path.unshift(node);
            node = previous[node];
        }

        return { distance: distances[endNode], path: path };
    }

    function ambulanceMeetsRequirements(ambulance, emergency) {
        if (emergency.severity === "Critical" && emergency.special_requirements.includes("Advanced Life Support")) {
            return ambulance.capabilities.includes("Advanced Life Support");
        }
        return true;
    }
  
    // 3. Ambulance Selection
    const graph = buildGraph(regions);
    let bestAmbulance = null;
    let minAmbulanceResponseTime = Infinity;

    for (const ambulance of ambulances) {
        if (ambulance.status === "Available" && ambulanceMeetsRequirements(ambulance, emergency_event)) {
            const ambulanceRegion = ambulance.current_region;
            const emergencyRegion = emergency_event.region_id;
            const route = dijkstra(graph, ambulanceRegion, emergencyRegion);
            const responseTime = route.distance;

            if (responseTime < minAmbulanceResponseTime) {
                minAmbulanceResponseTime = responseTime;
                bestAmbulance = ambulance;
            } else if (responseTime === minAmbulanceResponseTime) {
                // Prioritize by capabilities, then lower ID
                if (ambulance.capabilities.length > bestAmbulance.capabilities.length || ambulance.id < bestAmbulance.id) {
                    bestAmbulance = ambulance;
                }
            }
        }
    }

    if (bestAmbulance) {
        assignedAmbulance = bestAmbulance.id;
    } else {
        return {
            emergency_id: emergencyId,
            assigned_ambulance: null,
            destination_hospital: null
        };
    }

    // 4. Hospital Selection
    let bestHospital = null;
    let minHospitalArrivalTime = Infinity;

    for (const hospital of hospitals) {
        const hospitalRegion = hospital.region_id;
        const emergencyRegion = emergency_event.region_id;
        
        let meetsCapability = false;
        if (emergency_event.type === "Cardiac" && hospital.capabilities.includes("Cardiac Center")) {
            meetsCapability = true;
        } else if (emergency_event.type === "Trauma" && hospital.capabilities.includes("Trauma Center")) {
            meetsCapability = true;
        } else if (hospital.capabilities.includes("General Emergency")) {
            meetsCapability = true;
        }

        const route = dijkstra(graph, emergencyRegion, hospitalRegion);
        const arrivalTime = route.distance;

        if (meetsCapability) {
            if (arrivalTime < minHospitalArrivalTime) {
                minHospitalArrivalTime = arrivalTime;
                bestHospital = hospital;
            } else if (arrivalTime === minHospitalArrivalTime) {
                if (hospital.emergency_capacity === "High" && bestHospital.emergency_capacity !== "High") {
                    bestHospital = hospital;
                } else if (hospital.emergency_capacity === "Medium" && bestHospital.emergency_capacity === "Low") {
                    bestHospital = hospital;
                }
            }
        } else if (emergency_event.severity === "Critical" && arrivalTime < minHospitalArrivalTime) {
            minHospitalArrivalTime = arrivalTime;
            bestHospital = hospital;
        }
    }

    if (bestHospital) {
        destinationHospital = bestHospital.id;
    }

    // 5. Return Result
    return {
        emergency_id: emergencyId,
        assigned_ambulance: assignedAmbulance,
        destination_hospital: destinationHospital
    };
}

// Read input from stdin
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

let inputData = '';

rl.on('line', (line) => {
    inputData += line;
});

rl.on('close', () => {
    try {
        const { emergency_event, ambulances, hospitals, regions } = JSON.parse(inputData);
        const result = dispatchAmbulance(emergency_event, ambulances, hospitals, regions);
        console.log(JSON.stringify(result));
    } catch (error) {
        console.error("Error parsing JSON input:", error);
        console.log(JSON.stringify({
            emergency_id: null,
            assigned_ambulance: null,
            destination_hospital: null
        }));
    }
});