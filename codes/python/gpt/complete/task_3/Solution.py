import json
import sys
import heapq
from collections import defaultdict

def dijkstra(graph, start, end, blocked_routes):
    queue = [(0, start)]
    shortest_paths = {start: (None, 0)}
    visited = set()

    while queue:
        (cost, node) = heapq.heappop(queue)

        if node in visited:
            continue

        visited.add(node)

        if node == end:
            break

        for neighbor, weight in graph[node].items():
            if neighbor in visited or (node, neighbor) in blocked_routes:
                continue

            new_cost = cost + weight
            if neighbor not in shortest_paths or new_cost < shortest_paths[neighbor][1]:
                shortest_paths[neighbor] = (node, new_cost)
                heapq.heappush(queue, (new_cost, neighbor))

    path, total_cost = [], float('inf')
    if end in shortest_paths:
        total_cost = shortest_paths[end][1]
        while end is not None:
            path.append(end)
            end = shortest_paths[end][0]
        path = path[::-1]  # reverse path

    return total_cost, path

def build_graph(regions):
    graph = defaultdict(dict)
    for region in regions:
        region_id = region['region_id']
        speed = region['speed']
        congestion = region['congestion_factor']
        blocked_routes = set((region_id, b) for b in region['blocked_routes'])

        for neighbor, distance in region['distances'].items():
            if (region_id, neighbor) not in blocked_routes:
                travel_time = (distance / (speed * congestion)) * 60
                graph[region_id][neighbor] = travel_time

    return graph

def find_ambulance(emergency_event, ambulances, graph, blocked_routes):
    suitable_ambulances = []
    for ambulance in ambulances:
        if ambulance['status'] != 'Available':
            continue
        if emergency_event['severity'] == 'Critical' and 'Advanced Life Support' not in ambulance['capabilities']:
            continue
        if any(req not in ambulance['capabilities'] for req in emergency_event['special_requirements']):
            continue
        
        response_time, _ = dijkstra(graph, ambulance['current_region'], emergency_event['region_id'], blocked_routes)
        if response_time < float('inf'):
            suitable_ambulances.append((response_time, ambulance))

    if not suitable_ambulances:
        return None

    suitable_ambulances.sort(key=lambda x: (x[0], -len(x[1]['capabilities']), x[1]['id']))
    return suitable_ambulances[0][1]

def find_hospital(emergency_event, selected_ambulance, hospitals, graph, blocked_routes):
    suitable_hospitals = []
    for hospital in hospitals:
        if any(req not in hospital['capabilities'] for req in emergency_event['special_requirements']):
            continue
        
        hospital_time, _ = dijkstra(graph, emergency_event['region_id'], hospital['region_id'], blocked_routes)
        if hospital_time < float('inf'):
            suitable_hospitals.append((hospital_time, hospital))

    if not suitable_hospitals:
        return None

    suitable_hospitals.sort(key=lambda x: (-x[1]['emergency_capacity'] == 'High', -x[1]['emergency_capacity'] == 'Medium', x[0]))
    return suitable_hospitals[0][1]

def dispatch_ambulance(emergency_event, ambulances, hospitals, regions):
    graph = build_graph(regions)
    blocked_routes = {(r['region_id'], b) for r in regions for b in r['blocked_routes']}

    selected_ambulance = find_ambulance(emergency_event, ambulances, graph, blocked_routes)
    if not selected_ambulance:
        return {"emergency_id": emergency_event['id'], "assigned_ambulance": None, "destination_hospital": None}

    selected_hospital = find_hospital(emergency_event, selected_ambulance, hospitals, graph, blocked_routes)
    if not selected_hospital:
        return {"emergency_id": emergency_event['id'], "assigned_ambulance": selected_ambulance['id'], "destination_hospital": None}

    return {"emergency_id": emergency_event['id'], "assigned_ambulance": selected_ambulance['id'], "destination_hospital": selected_hospital['id']}

def main():
    input_data = json.loads(sys.stdin.read())
    emergency_event = input_data['emergency_event']
    ambulances = input_data['ambulances']
    hospitals = input_data['hospitals']
    regions = input_data['regions']

    result = dispatch_ambulance(emergency_event, ambulances, hospitals, regions)
    print(json.dumps(result))

if __name__ == "__main__":
    main()