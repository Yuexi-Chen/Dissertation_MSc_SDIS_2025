import json
import heapq

def calculate_travel_time(distance, region_type, congestion_factor):
    if region_type == "Urban":
        base_speed = 30
    elif region_type == "Suburban":
        base_speed = 50
    else:  # Rural
        base_speed = 80
    
    travel_time = (distance / (base_speed * congestion_factor)) * 60
    return travel_time

def build_graph(regions):
    graph = {}
    for region in regions:
        graph[region["region_id"]] = {}
        for neighbor, distance in region["distances"].items():
            if neighbor not in graph:
                continue
            travel_time = calculate_travel_time(distance, region["type"], region["congestion_factor"])

            if neighbor in region["blocked_routes"]:
                travel_time = float('inf')
            
            graph[region["region_id"]][neighbor] = travel_time
            
    return graph

def dijkstra(graph, start, end, available_nodes):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    priority_queue = [(0, start)]  # (distance, node)
    
    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        
        if current_distance > distances[current_node]:
            continue
        
        if current_node == end:
            return distances[end]
        
        for neighbor, weight in graph[current_node].items():
            if neighbor not in available_nodes:
                continue
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(priority_queue, (distance, neighbor))
    
    return float('inf')

def dispatch_ambulance(emergency_event, ambulances, hospitals, regions):
    emergency_id = emergency_event["id"]
    event_region = emergency_event["region_id"]
    severity = emergency_event["severity"]
    emergency_type = emergency_event["type"]
    special_requirements = emergency_event["special_requirements"]

    graph = build_graph(regions)
    available_regions = list(graph.keys())

    # Step 1: Select the fastest ambulance
    best_ambulance = None
    min_ambulance_time = float('inf')

    for ambulance in ambulances:
        if ambulance["status"] == "Available":
            ambulance_id = ambulance["id"]
            ambulance_region = ambulance["current_region"]
            ambulance_capabilities = ambulance["capabilities"]

            # Check capability requirements for critical emergencies
            if severity == "Critical" and "Advanced Life Support" in special_requirements and "Advanced Life Support" not in ambulance_capabilities and "Defibrillator" not in ambulance_capabilities:
                continue  # Skip if ambulance lacks required capabilities

            ambulance_time = dijkstra(graph, ambulance_region, event_region, available_regions)

            if ambulance_time < min_ambulance_time:
                min_ambulance_time = ambulance_time
                best_ambulance = ambulance
            elif ambulance_time == min_ambulance_time and best_ambulance is not None:
                # Prioritize by capabilities, then lower ID
                best_ambulance_capabilities = best_ambulance["capabilities"]
                if severity == "Critical" and "Advanced Life Support" in special_requirements:
                    if "Advanced Life Support" in ambulance_capabilities and "Advanced Life Support" not in best_ambulance_capabilities:
                        best_ambulance = ambulance
                    elif "Advanced Life Support" in best_ambulance_capabilities and "Advanced Life Support" not in ambulance_capabilities:
                        pass
                    elif ambulance["id"] < best_ambulance["id"]:
                        best_ambulance = ambulance
                elif ambulance["id"] < best_ambulance["id"]:
                    best_ambulance = ambulance

    # Step 2: Choose the best hospital
    best_hospital = None
    min_hospital_time = float('inf')

    if best_ambulance:
        for hospital in hospitals:
            hospital_region = hospital["region_id"]
            hospital_capabilities = hospital["capabilities"]
            emergency_capacity = hospital["emergency_capacity"]
            
            # Filter by matching capabilities
            hospital_match = False
            if emergency_type == "Cardiac" and "Cardiac Center" in hospital_capabilities:
                hospital_match = True
            elif emergency_type == "Trauma" and "Trauma Center" in hospital_capabilities:
                hospital_match = True
            elif emergency_type == "Stroke" and "Stroke Unit" in hospital_capabilities:
                hospital_match = True
            elif "General Emergency" in hospital_capabilities:
                hospital_match = True

            if not hospital_match and severity != "Critical":
                continue
            
            ambulance_to_hospital_time = dijkstra(graph, event_region, hospital_region, available_regions)

            if ambulance_to_hospital_time < min_hospital_time:
                min_hospital_time = ambulance_to_hospital_time
                best_hospital = hospital
            elif ambulance_to_hospital_time == min_hospital_time and best_hospital is not None:
                # Prioritize by emergency capacity (High > Medium > Low)
                capacity_priority = {"High": 3, "Medium": 2, "Low": 1}
                if capacity_priority[emergency_capacity] > capacity_priority[best_hospital["emergency_capacity"]]:
                    best_hospital = hospital

    result = {
        "emergency_id": emergency_id,
        "assigned_ambulance": best_ambulance["id"] if best_ambulance else None,
        "destination_hospital": best_hospital["id"] if best_hospital else None
    }

    return result

if __name__ == "__main__":
    input_json = json.load(input())
    emergency_event = input_json["emergency_event"]
    ambulances = input_json["ambulances"]
    hospitals = input_json["hospitals"]
    regions = input_json["regions"]
    
    result = dispatch_ambulance(emergency_event, ambulances, hospitals, regions)
    print(json.dumps(result))