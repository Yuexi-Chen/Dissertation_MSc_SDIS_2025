import sys
import json
from itertools import permutations

def allocate_resources(patients, resources, responders, total_time):
    n_patients = len(patients)
    n_resources = len(resources)
    
    best_assignments = []
    best_survival_prob = 0
    survivors = 0
    
    # Try all permutations of resources and patients within total_time
    for perm in permutations(range(n_patients)):
        current_time = 0
        current_assignments = []
        current_survival_prob = 0
        current_survivors = 0
        responder_available_time = [0] * responders
        
        for patient_index in perm:
            if current_time >= total_time:
                break
            
            patient_probs = patients[patient_index]
            max_prob = 0
            best_resource = None
            best_time = None
            
            # Go through all resources to find the best one
            for resource_index, resource in enumerate(resources):
                time_needed = resource['time']
                boost = resource['boost']
                
                # Find the earliest time a responder is available and the treatment can be started
                for time in range(current_time, total_time):
                    if time + time_needed > total_time:
                        break
                    if time < len(patient_probs) and all(responder_available_time[i] <= time for i in range(responders)):
                        prob = patient_probs[time] + boost
                        if prob > max_prob and prob <= 100:  # Ensure probability does not exceed 100
                            max_prob = prob
                            best_resource = resource_index
                            best_time = time
            
            if best_resource is not None:
                current_assignments.append({"patient": patient_index, "resource": best_resource, "time": best_time})
                current_survival_prob += max_prob
                if max_prob >= 50:  # Consider patient as survivor if boosted probability is 50 or more
                    current_survivors += 1
                
                # Set the responder available time
                for i in range(responders):
                    if responder_available_time[i] <= best_time:
                        responder_available_time[i] = best_time + resources[best_resource]['time']
                        break
            
            current_time += 1
        
        if current_survival_prob > best_survival_prob:
            best_survival_prob = current_survival_prob
            best_assignments = current_assignments
            survivors = current_survivors
    
    return {
        "assignments": best_assignments,
        "survivors": survivors,
        "total_survival_probability": best_survival_prob
    }

def main():
    input_data = json.load(sys.stdin)
    patients = input_data['patients']
    resources = input_data['resources']
    responders = input_data['responders']
    total_time = input_data['total_time']
    
    result = allocate_resources(patients, resources, responders, total_time)
    print(json.dumps(result))

if __name__ == "__main__":
    main()