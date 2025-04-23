import json
import heapq
import math

def calculate_travel_time(distance, region_type, congestion_factor):
    """Calculates travel time in minutes based on distance, region type, and congestion factor."""
    if region_type == "Urban":
        base_speed = 30
    elif region_type == "Suburban":
        base_speed = 50
    else:  # Rural
        base_speed = 80
    
    if congestion_factor <= 0:
        return float('inf')  # Handle invalid congestion factors
    
    travel_time = (distance / (base_speed * congestion_factor)) * 60
    return travel_time

def build_graph(regions):
    """Builds a graph representation from the region data."""
    graph = {}
    for region in regions:
        region_id = region["region_id"]
        graph[region_id] = {}
        for neighbor_id, distance in region["distances"].items():
            if neighbor_id in region["blocked_routes"]:
                graph[region_id][neighbor_id] = float('inf')
            else:
                travel_time = calculate_travel_time(distance, region["type"], region["congestion_factor"])
                graph[region_id][neighbor_id] = travel_time
    return graph

def dijkstra(graph, start, end=None):
    """
    Implements Dijkstra's algorithm to find the shortest path from a start node to all other nodes or to a specific end node.
    Returns a dictionary of shortest distances from the start node to all other nodes.
    If an end node is specified, returns only the shortest distance to that node.
    """
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    priority_queue = [(0, start)]  # (distance, node)

    while priority_queue:
        dist, current_node = heapq.heappop(priority_queue)

        if dist > distances[current_node]:
            continue

        if end is not None and current_node == end:
            return distances[end]
        
        for neighbor, weight in graph[current_node].items():
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(priority_queue, (new_dist, neighbor))

    return distances

def find_fastest_ambulance(emergency_event, ambulances, regions):
    """Finds the fastest available ambulance that meets the emergency's capability requirements."""
    graph = build_graph(regions)
    emergency_region = emergency_event["region_id"]
    
    eligible_ambulances = []
    for ambulance in ambulances:
        if ambulance["status"] == "Available":
            if emergency_event["severity"] == "Critical" and "Advanced Life Support" in emergency_event["special_requirements"]:
                if "Advanced Life Support" in ambulance["capabilities"] or "Defibrillator" in ambulance["capabilities"]:
                    eligible_ambulances.append(ambulance)
            else:
                eligible_ambulances.append(ambulance)
    
    if not eligible_ambulances:
        return None

    fastest_ambulance = None
    min_response_time = float('inf')

    for ambulance in eligible_ambulances:
        ambulance_region = ambulance["current_region"]
        if ambulance_region == emergency_region:
            response_time = 0
        else:
            response_time = dijkstra(graph, ambulance_region, emergency_region)
        
        if response_time < min_response_time:
            min_response_time = response_time
            fastest_ambulance = ambulance
        elif response_time == min_response_time:
            # Prioritize by capabilities, then lower ID
            if emergency_event["severity"] == "Critical" and "Advanced Life Support" in emergency_event["special_requirements"]:
                if ("Advanced Life Support" in ambulance["capabilities"] or "Defibrillator" in ambulance["capabilities"]) and (fastest_ambulance is None or ("Advanced Life Support" not in fastest_ambulance["capabilities"] and "Defibrillator" not in fastest_ambulance["capabilities"])):
                    fastest_ambulance = ambulance
                elif ambulance["id"] < fastest_ambulance["id"]:
                    fastest_ambulance = ambulance
            elif ambulance["id"] < fastest_ambulance["id"]:
                fastest_ambulance = ambulance
    
    return fastest_ambulance

def find_best_hospital(emergency_event, ambulance, hospitals, regions):
    """Finds the best hospital for the given emergency and ambulance."""
    graph = build_graph(regions)
    emergency_region = emergency_event["region_id"]

    eligible_hospitals = []
    for hospital in hospitals:
        if emergency_event["type"] == "Cardiac" and "Cardiac Center" in hospital["capabilities"]:
            eligible_hospitals.append(hospital)
        elif emergency_event["type"] == "Trauma" and "Trauma Center" in hospital["capabilities"]:
            eligible_hospitals.append(hospital)
        elif emergency_event["type"] == "Stroke" and "Stroke Unit" in hospital["capabilities"]:
            eligible_hospitals.append(hospital)
        else:
             eligible_hospitals.append(hospital)
    
    if not eligible_hospitals:
        return None

    best_hospital = None
    min_arrival_time = float('inf')

    for hospital in eligible_hospitals:
        hospital_region = hospital["region_id"]
        if emergency_region == hospital_region:
            arrival_time = 0
        else:
            arrival_time = dijkstra(graph, emergency_region, hospital_region)
        
        if emergency_event["severity"] == "Critical":
            if arrival_time < min_arrival_time:
                min_arrival_time = arrival_time
                best_hospital = hospital
        else:
            if arrival_time < min_arrival_time:
                min_arrival_time = arrival_time
                best_hospital = hospital
            elif arrival_time == min_arrival_time:
                # Prioritize emergency capacity (High > Medium > Low)
                capacity_priority = {"High": 3, "Medium": 2, "Low": 1}
                if capacity_priority[hospital["emergency_capacity"]] > capacity_priority.get(best_hospital["emergency_capacity"],0):
                    best_hospital = hospital

    return best_hospital

def dispatch_ambulance(emergency_event, ambulances, hospitals, regions):
    """Dispatches an ambulance to an emergency event and selects the best hospital."""
    assigned_ambulance = find_fastest_ambulance(emergency_event, ambulances, regions)
    
    if assigned_ambulance:
        destination_hospital = find_best_hospital(emergency_event, assigned_ambulance, hospitals, regions)
        
        if destination_hospital:
            return {
                "emergency_id": emergency_event["id"],
                "assigned_ambulance": assigned_ambulance["id"],
                "destination_hospital": destination_hospital["id"]
            }
        else:
             return {
                "emergency_id": emergency_event["id"],
                "assigned_ambulance": assigned_ambulance["id"],
                "destination_hospital": None
            }
    else:
        return {
            "emergency_id": emergency_event["id"],
            "assigned_ambulance": None,
            "destination_hospital": None
        }

def main():
    """Reads input from stdin, calls dispatch_ambulance, and prints the result as JSON."""
    input_data = json.loads(input())
    emergency_event = input_data["emergency_event"]
    ambulances = input_data["ambulances"]
    hospitals = input_data["hospitals"]
    regions = input_data["regions"]

    result = dispatch_ambulance(emergency_event, ambulances, hospitals, regions)
    print(json.dumps(result))

if __name__ == "__main__":
    main()