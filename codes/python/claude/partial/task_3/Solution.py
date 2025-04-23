import json
import sys
from typing import Dict, List
from math import inf

def dispatch_ambulance(emergency_event: Dict, ambulances: List[Dict], hospitals: List[Dict], regions: List[Dict]) -> Dict:
    def calculate_travel_time(start: str, end: str) -> float:
        if start == end:
            return 0
        
        start_region = next(r for r in regions if r['region_id'] == start)
        end_region = next(r for r in regions if r['region_id'] == end)
        
        if end in start_region['blocked_routes']:
            return inf
        
        distance = start_region['distances'].get(end, inf)
        base_speed = start_region['speed']
        congestion_factor = start_region['congestion_factor']
        
        return (distance / (base_speed * congestion_factor)) * 60

    def dijkstra(start: str, end: str) -> float:
        distances = {r['region_id']: inf for r in regions}
        distances[start] = 0
        unvisited = set(distances.keys())
        
        while unvisited:
            current = min(unvisited, key=lambda x: distances[x])
            if current == end:
                return distances[end]
            unvisited.remove(current)
            
            for neighbor in unvisited:
                time = calculate_travel_time(current, neighbor)
                if time < inf:
                    new_distance = distances[current] + time
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
        
        return inf

    def select_ambulance() -> Dict:
        suitable_ambulances = [
            a for a in ambulances if a['status'] == 'Available' and
            (set(emergency_event['special_requirements']).issubset(set(a['capabilities'])) or
             (emergency_event['severity'] == 'Critical' and 'Advanced Life Support' in a['capabilities']))
        ]
        
        if not suitable_ambulances:
            return None
        
        return min(suitable_ambulances, key=lambda a: (
            dijkstra(a['current_region'], emergency_event['region_id']),
            -len(a['capabilities']),
            a['id']
        ))

    def select_hospital(ambulance: Dict) -> Dict:
        suitable_hospitals = [
            h for h in hospitals if
            (emergency_event['type'] in h['capabilities'] or
             (emergency_event['severity'] == 'Critical' and any(cap in h['capabilities'] for cap in ['Trauma Center', 'Cardiac Center', 'Stroke Unit'])))
        ]
        
        if not suitable_hospitals:
            return None
        
        return min(suitable_hospitals, key=lambda h: (
            dijkstra(emergency_event['region_id'], h['region_id']),
            -['Low', 'Medium', 'High'].index(h['emergency_capacity']),
            h['id']
        ))

    selected_ambulance = select_ambulance()
    if not selected_ambulance:
        return {"emergency_id": emergency_event['id'], "assigned_ambulance": None, "destination_hospital": None}

    selected_hospital = select_hospital(selected_ambulance)
    if not selected_hospital:
        return {"emergency_id": emergency_event['id'], "assigned_ambulance": None, "destination_hospital": None}

    return {
        "emergency_id": emergency_event['id'],
        "assigned_ambulance": selected_ambulance['id'],
        "destination_hospital": selected_hospital['id']
    }

def main():
    input_data = json.loads(sys.stdin.read())
    result = dispatch_ambulance(
        input_data['emergency_event'],
        input_data['ambulances'],
        input_data['hospitals'],
        input_data['regions']
    )
    print(json.dumps(result))

if __name__ == "__main__":
    main()