import json
import sys
import heapq
from math import inf

def dispatch_ambulance(emergency_event, ambulances, hospitals, regions):
    graph = build_graph(regions)
    
    # Step 1: Select the fastest ambulance
    best_ambulance = select_ambulance(emergency_event, ambulances, graph)
    if not best_ambulance:
        return {"emergency_id": emergency_event["id"], "assigned_ambulance": None, "destination_hospital": None}
    
    # Step 2: Select the best hospital
    best_hospital = select_hospital(emergency_event, best_ambulance, hospitals, graph)
    if not best_hospital:
        return {"emergency_id": emergency_event["id"], "assigned_ambulance": None, "destination_hospital": None}
    
    return {
        "emergency_id": emergency_event["id"],
        "assigned_ambulance": best_ambulance["id"],
        "destination_hospital": best_hospital["id"]
    }

def build_graph(regions):
    graph = {}
    for region in regions:
        graph[region["region_id"]] = {}
        for neighbor, distance in region["distances"].items():
            if neighbor not in region["blocked_routes"]:
                travel_time = calculate_travel_time(distance, region["speed"], region["congestion_factor"])
                graph[region["region_id"]][neighbor] = travel_time
    return graph

def calculate_travel_time(distance, speed, congestion_factor):
    return round((distance / (speed * congestion_factor)) * 60)

def dijkstra(graph, start, end):
    distances = {node: inf for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    
    while pq:
        current_distance, current_node = heapq.heappop(pq)
        
        if current_node == end:
            return current_distance
        
        if current_distance > distances[current_node]:
            continue
        
        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return inf

def select_ambulance(emergency, ambulances, graph):
    suitable_ambulances = []
    for ambulance in ambulances:
        if emergency["severity"] == "Critical" and "Advanced Life Support" not in ambulance["capabilities"]:
            continue
        if set(emergency["special_requirements"]).issubset(set(ambulance["capabilities"])):
            response_time = dijkstra(graph, ambulance["current_region"], emergency["region_id"])
            suitable_ambulances.append((response_time, ambulance))
    
    if not suitable_ambulances:
        return None
    
    return min(suitable_ambulances, key=lambda x: (x[0], -len(x[1]["capabilities"]), x[1]["id"]))[1]

def select_hospital(emergency, ambulance, hospitals, graph):
    suitable_hospitals = []
    for hospital in hospitals:
        if emergency["severity"] == "Critical" or set(emergency["special_requirements"]).issubset(set(hospital["capabilities"])):
            hospital_time = dijkstra(graph, emergency["region_id"], hospital["region_id"])
            suitable_hospitals.append((hospital_time, hospital))
    
    if not suitable_hospitals:
        return None
    
    return min(suitable_hospitals, key=lambda x: (x[0], -["Low", "Medium", "High"].index(x[1]["emergency_capacity"])))[1]

def main():
    input_data = json.loads(sys.stdin.read())
    result = dispatch_ambulance(
        input_data["emergency_event"],
        input_data["ambulances"],
        input_data["hospitals"],
        input_data["regions"]
    )
    print(json.dumps(result))

if __name__ == "__main__":
    main()