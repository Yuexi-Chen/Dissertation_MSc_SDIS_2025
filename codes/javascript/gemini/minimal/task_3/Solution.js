const process = require('process');

function dispatchAmbulance(emergency_event, ambulances, hospitals, regions) {
    const { id: emergency_id, region_id: emergency_region, severity, type, special_requirements } = emergency_event;

    // 2. Algorithm Implementation (Using Graph):
    //    a. Graph Construction:
    //       - Regions are nodes; distances form edges with weights calculated as travel times
    //       - Edge weight: Travel Time = Distance (km) / (Base Speed * Congestion Factor) * 60 minutes
    //         * Base Speed: Urban = 30 km/h, Suburban = 50 km/h, Rural = 80 km/h
    //         * Congestion Factor between 0-1 (1 = no congestion, 0.5 = 50% slower)
    //       - Assign infinite weight to blocked routes

    function calculateTravelTime(distance, regionType, congestionFactor) {
        let baseSpeed;
        switch (regionType) {
            case "Urban":
                baseSpeed = 30;
                break;
            case "Suburban":
                baseSpeed = 50;
                break;
            case "Rural":
                baseSpeed = 80;
                break;
            default:
                return Infinity; // Unknown region type
        }
        return distance / (baseSpeed * congestionFactor) * 60;
    }

    function buildGraph(regions) {
        const graph = {};
        regions.forEach(region => {
            graph[region.region_id] = {};
            for (const neighbor in region.distances) {
                if (region.blocked_routes.includes(neighbor)) {
                    graph[region.region_id][neighbor] = Infinity;
                } else {
                    graph[region.region_id][neighbor] = calculateTravelTime(
                        region.distances[neighbor],
                        region.type,
                        region.congestion_factor
                    );
                }
            }
        });
        return graph;
    }

    function dijkstra(graph, start, end) {
        const distances = {};
        const visited = {};
        const previous = {};
        for (const node in graph) {
            distances[node] = Infinity;
            visited[node] = false;
            previous[node] = null;
        }
        distances[start] = 0;

        while (true) {
            let closestNode = null;
            let shortestDistance = Infinity;
            for (const node in distances) {
                if (!visited[node] && distances[node] < shortestDistance) {
                    closestNode = node;
                    shortestDistance = distances[node];
                }
            }

            if (closestNode === null) {
                break;
            }

            visited[closestNode] = true;

            for (const neighbor in graph[closestNode]) {
                const distance = distances[closestNode] + graph[closestNode][neighbor];
                if (distance < distances[neighbor]) {
                    distances[neighbor] = distance;
                    previous[neighbor] = closestNode;
                }
            }
        }

        let path = [];
        let current = end;
        while (current !== null) {
            path.unshift(current);
            current = previous[current];
        }

        if (distances[end] === Infinity) {
            return { distance: Infinity, path: [] };
        }

        return { distance: distances[end], path: path };
    }

    const graph = buildGraph(regions);

    //    b. Two-Step Process (Fixed Order):
    //       - Step 1: Select the fastest ambulance that meets capability requirements using Dijkstra's algorithm
    //         * For tied arrival times, prioritize by capabilities, then lower ID
    //         * Critical emergencies require Advanced Life Support capabilities

    let bestAmbulance = null;
    let shortestAmbulanceTime = Infinity;

    for (const ambulance of ambulances) {
        if (ambulance.status === "Available") {
            let meetsRequirements = true;
            if (severity === "Critical" && special_requirements.includes("Advanced Life Support")) {
                if (!ambulance.capabilities.includes("Advanced Life Support") && !ambulance.capabilities.includes("Defibrillator")) {
                    meetsRequirements = false;
                }
            }

            if (meetsRequirements) {
                const ambulanceRoute = dijkstra(graph, ambulance.current_region, emergency_region);
                if (ambulanceRoute.distance < shortestAmbulanceTime) {
                    shortestAmbulanceTime = ambulanceRoute.distance;
                    bestAmbulance = ambulance;
                } else if (ambulanceRoute.distance === shortestAmbulanceTime) {
                    // Prioritize by capabilities, then lower ID
                    if (bestAmbulance && ambulance.capabilities.length > bestAmbulance.capabilities.length) {
                        bestAmbulance = ambulance;
                    } else if (bestAmbulance && ambulance.id < bestAmbulance.id) {
                        bestAmbulance = ambulance;
                    }
                }
            }
        }
    }

    if (!bestAmbulance) {
        return { emergency_id: emergency_id, assigned_ambulance: null, destination_hospital: null };
    }

    //       - Step 2: Using the selected ambulance, choose the best hospital using Dijkstra's algorithm
    //         * Filter by matching capabilities (Cardiac Center for cardiac cases, etc.)
    //         * Prioritize by emergency capacity (High > Medium > Low)
    //         * For Critical emergencies, prioritize response time over exact capability matching
    //         * Never reconsider ambulance selection even if no perfect hospital match exists

    let bestHospital = null;
    let shortestHospitalTime = Infinity;

    for (const hospital of hospitals) {
        let meetsRequirements = true;

        if (type === "Cardiac" && !hospital.capabilities.includes("Cardiac Center")) {
            meetsRequirements = false;
        }

        if (meetsRequirements) {
            const hospitalRoute = dijkstra(graph, emergency_region, hospital.region_id);
            if (hospitalRoute.distance < shortestHospitalTime) {
                shortestHospitalTime = hospitalRoute.distance;
                bestHospital = hospital;
            } else if (hospitalRoute.distance === shortestHospitalTime) {
                // Prioritize by emergency capacity (High > Medium > Low)
                if (bestHospital) {
                    const capacityOrder = { "High": 3, "Medium": 2, "Low": 1 };
                    if (capacityOrder[hospital.emergency_capacity] > capacityOrder[bestHospital.emergency_capacity]) {
                        bestHospital = hospital;
                    }
                }
            }
        }
    }

    if (severity === "Critical" && !bestHospital) {
      for (const hospital of hospitals) {
        const hospitalRoute = dijkstra(graph, emergency_region, hospital.region_id);
        if (hospitalRoute.distance < shortestHospitalTime) {
            shortestHospitalTime = hospitalRoute.distance;
            bestHospital = hospital;
        } else if (hospitalRoute.distance === shortestHospitalTime) {
            // Prioritize by emergency capacity (High > Medium > Low)
            if (bestHospital) {
                const capacityOrder = { "High": 3, "Medium": 2, "Low": 1 };
                if (capacityOrder[hospital.emergency_capacity] > capacityOrder[bestHospital.emergency_capacity]) {
                    bestHospital = hospital;
                }
            }
        }
      }
    }

    return {
        emergency_id: emergency_id,
        assigned_ambulance: bestAmbulance ? bestAmbulance.id : null,
        destination_hospital: bestHospital ? bestHospital.id : null
    };
}

// Input/Output Requirements:
//    a. Do NOT modify the input data structures
//    b. Always return a complete object with: emergency_id, assigned_ambulance, destination_hospital
//    c. When no assignment is possible, return fields as null but maintain the object structure
//    d. Follow the exact output format shown in the examples
process.stdin.setEncoding('utf8');

let input = '';

process.stdin.on('data', function(chunk) {
    input += chunk;
});

process.stdin.on('end', function() {
    try {
        const data = JSON.parse(input);
        const result = dispatchAmbulance(data.emergency_event, data.ambulances, data.hospitals, data.regions);
        console.log(JSON.stringify(result));
    } catch (error) {
        console.error("Error processing input:", error);
    }
});