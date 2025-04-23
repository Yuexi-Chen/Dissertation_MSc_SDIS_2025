const readline = require('readline');

function dispatchAmbulance(emergency_event, ambulances, hospitals, regions) {
    function calculateTravelTime(distance, regionType, congestionFactor) {
        let baseSpeed;
        switch (regionType) {
            case 'Urban':
                baseSpeed = 30;
                break;
            case 'Suburban':
                baseSpeed = 50;
                break;
            case 'Rural':
                baseSpeed = 80;
                break;
            default:
                baseSpeed = 50;
        }
        return Math.round((distance / (baseSpeed * congestionFactor)) * 60);
    }

    function buildGraph(regions) {
        const graph = {};
        regions.forEach(region => {
            graph[region.region_id] = {};
            for (const neighbor in region.distances) {
                if (!region.blocked_routes.includes(neighbor)) {
                    const travelTime = calculateTravelTime(
                        region.distances[neighbor],
                        region.type,
                        region.congestion_factor
                    );
                    graph[region.region_id][neighbor] = travelTime;
                } else {
                    graph[region.region_id][neighbor] = Infinity;
                }
            }
        });
        return graph;
    }

    function dijkstra(graph, start, end) {
        const distances = {};
        const visited = {};
        for (const node in graph) {
            distances[node] = Infinity;
        }
        distances[start] = 0;

        while (true) {
            let closestNode = null;
            for (const node in graph) {
                if (!visited[node] && (closestNode === null || distances[node] < distances[closestNode])) {
                    closestNode = node;
                }
            }

            if (closestNode === null) {
                break;
            }

            visited[closestNode] = true;

            for (const neighbor in graph[closestNode]) {
                const distance = graph[closestNode][neighbor];
                if (distances[closestNode] + distance < distances[neighbor]) {
                    distances[neighbor] = distances[closestNode] + distance;
                }
            }
        }

        return distances[end];
    }

    const graph = buildGraph(regions);
    const emergencyRegion = emergency_event.region_id;
    const requiredCapabilities = emergency_event.special_requirements;
    const isCritical = emergency_event.severity === 'Critical';

    let bestAmbulance = null;
    let minAmbulanceTime = Infinity;

    for (const ambulance of ambulances) {
        if (ambulance.status === 'Available') {
            let meetsRequirements = true;
            if (isCritical && !ambulance.capabilities.includes('Advanced Life Support')) {
                meetsRequirements = false;
            } else {
                for (const requirement of requiredCapabilities) {
                    if (!ambulance.capabilities.includes(requirement)) {
                        meetsRequirements = false;
                        break;
                    }
                }
            }


            if (meetsRequirements) {
                const ambulanceRegion = ambulance.current_region;
                const timeToEmergency = ambulanceRegion === emergencyRegion ? 0 : dijkstra(graph, ambulanceRegion, emergencyRegion);

                if (timeToEmergency < minAmbulanceTime) {
                    minAmbulanceTime = timeToEmergency;
                    bestAmbulance = ambulance;
                } else if (timeToEmergency === minAmbulanceTime) {
                    if (ambulance.capabilities.length > bestAmbulance.capabilities.length) {
                        bestAmbulance = ambulance;
                    } else if (ambulance.id < bestAmbulance.id) {
                        bestAmbulance = ambulance;
                    }
                }
            }
        }
    }

    if (!bestAmbulance) {
        return {
            emergency_id: emergency_event.id,
            assigned_ambulance: null,
            destination_hospital: null
        };
    }

    let bestHospital = null;
    let minHospitalTime = Infinity;

    for (const hospital of hospitals) {
        let meetsRequirements = true;

        if (emergency_event.type === 'Cardiac' && !hospital.capabilities.includes('Cardiac Center')) {
            meetsRequirements = false;
        }

        if (emergency_event.type === 'Trauma' && !hospital.capabilities.includes('Trauma Center')) {
            meetsRequirements = false;
        }

        if (meetsRequirements) {
            const hospitalRegion = hospital.region_id;
            const timeToHospital = emergencyRegion === hospitalRegion ? 0 : dijkstra(graph, emergencyRegion, hospitalRegion);

            if (timeToHospital < minHospitalTime) {
                minHospitalTime = timeToHospital;
                bestHospital = hospital;
            } else if (timeToHospital === minHospitalTime) {
                if (hospital.emergency_capacity === 'High' && bestHospital.emergency_capacity !== 'High') {
                    bestHospital = hospital;
                } else if (hospital.emergency_capacity === 'Medium' && bestHospital.emergency_capacity !== 'High' && bestHospital.emergency_capacity !== 'Medium') {
                    bestHospital = hospital;
                }
            }
        }
    }

    if (!bestHospital) {
        let nearestHospital = null;
        let minTime = Infinity;
        for (const hospital of hospitals) {
            const hospitalRegion = hospital.region_id;
            const timeToHospital = emergencyRegion === hospitalRegion ? 0 : dijkstra(graph, emergencyRegion, hospitalRegion);
            if (timeToHospital < minTime) {
                minTime = timeToHospital;
                nearestHospital = hospital;
            }
        }
        bestHospital = nearestHospital;
    }

    return {
        emergency_id: emergency_event.id,
        assigned_ambulance: bestAmbulance.id,
        destination_hospital: bestHospital.id
    };
}


if (require.main === module) {
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
            const input = JSON.parse(inputData);
            const result = dispatchAmbulance(input.emergency_event, input.ambulances, input.hospitals, input.regions);
            console.log(JSON.stringify(result));
        } catch (error) {
            console.error('Error parsing JSON input:', error);
            console.log(JSON.stringify({
                emergency_id: null,
                assigned_ambulance: null,
                destination_hospital: null
            }));
        }
    });
}