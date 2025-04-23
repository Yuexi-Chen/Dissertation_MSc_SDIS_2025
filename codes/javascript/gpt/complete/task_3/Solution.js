function dispatchAmbulance(emergency_event, ambulances, hospitals, regions) {
    const INF = Number.MAX_SAFE_INTEGER;

    function calculateTravelTime(distance, regionType, congestionFactor) {
        const baseSpeeds = { "Urban": 30, "Suburban": 50, "Rural": 80 };
        const speed = baseSpeeds[regionType];
        return Math.round((distance / (speed * congestionFactor)) * 60);
    }

    function buildGraph() {
        const graph = {};
        regions.forEach(region => {
            const { region_id, type, distances, congestion_factor, blocked_routes } = region;
            graph[region_id] = {};
            for (const [neighbor, distance] of Object.entries(distances)) {
                if (!blocked_routes.includes(neighbor)) {
                    graph[region_id][neighbor] = calculateTravelTime(distance, type, congestion_factor);
                }
            }
        });
        return graph;
    }

    function dijkstra(graph, start, end) {
        const times = {};
        const pq = new MinPriorityQueue({ priority: x => x[1] });
        pq.enqueue([start, 0]);
        times[start] = 0;

        while (!pq.isEmpty()) {
            const [node, time] = pq.dequeue().element;
            if (node === end) break;
            if (time > times[node]) continue;

            for (const [neighbor, travelTime] of Object.entries(graph[node])) {
                const newTime = time + travelTime;
                if (newTime < (times[neighbor] || INF)) {
                    times[neighbor] = newTime;
                    pq.enqueue([neighbor, newTime]);
                }
            }
        }
        return times[end] || INF;
    }

    function findBestAmbulance() {
        let bestAmbulance = null;
        let bestTime = INF;

        ambulances.forEach(ambulance => {
            if (ambulance.status !== "Available") return;

            const hasAllCapabilities = emergency_event.special_requirements.every(req =>
                ambulance.capabilities.includes(req)
            );

            if (!hasAllCapabilities) return;

            const travelTime = dijkstra(graph, ambulance.current_region, emergency_event.region_id);

            if (travelTime < bestTime || (travelTime === bestTime && ambulance.id < bestAmbulance.id)) {
                bestAmbulance = ambulance;
                bestTime = travelTime;
            }
        });

        return bestAmbulance;
    }

    function findBestHospital(ambulance) {
        let bestHospital = null;
        let bestTime = INF;

        hospitals.forEach(hospital => {
            const hasRequiredCapabilities = emergency_event.type === "Critical" || hospital.capabilities.includes(emergency_event.type);
            if (!hasRequiredCapabilities) return;

            const travelTime = dijkstra(graph, emergency_event.region_id, hospital.region_id);

            if (travelTime < bestTime || 
                (travelTime === bestTime && hospital.emergency_capacity > (bestHospital ? bestHospital.emergency_capacity : "Low"))) {
                bestHospital = hospital;
                bestTime = travelTime;
            }
        });

        return bestHospital;
    }

    const graph = buildGraph();
    const bestAmbulance = findBestAmbulance();
    if (!bestAmbulance) {
        return { emergency_id: emergency_event.id, assigned_ambulance: null, destination_hospital: null };
    }

    const bestHospital = findBestHospital(bestAmbulance);
    return {
        emergency_id: emergency_event.id,
        assigned_ambulance: bestAmbulance ? bestAmbulance.id : null,
        destination_hospital: bestHospital ? bestHospital.id : null
    };
}

const input = JSON.parse(require('fs').readFileSync(0, 'utf-8'));
const result = dispatchAmbulance(input.emergency_event, input.ambulances, input.hospitals, input.regions);
console.log(JSON.stringify(result));