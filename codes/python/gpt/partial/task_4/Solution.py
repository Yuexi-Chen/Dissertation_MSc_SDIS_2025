import json
import sys
from itertools import product

def allocate_resources(patients, resources, responders, total_time):
    num_patients = len(patients)
    num_resources = len(resources)
    
    # This will store the best assignments found
    best_assignments = []
    best_survivors = 0
    best_total_survival_probability = 0
    
    # Helper function to calculate survival probability
    def calculate_probability(patient_probs, resource, start_time):
        if start_time + resource['time'] > len(patient_probs):
            return 0
        initial_prob = patient_probs[start_time]
        boosted_prob = min(100, initial_prob + resource['boost'])
        return boosted_prob
    
    # Try all possible assignments of resources to patients and time
    for assignment in product(range(num_patients), range(num_resources), range(total_time)):
        patient, resource_idx, time = assignment
        resource = resources[resource_idx]
        
        if time + resource['time'] > total_time:
            continue
        
        # Calculate the survival probability if this resource is used at this time
        final_probability = calculate_probability(patients[patient], resource, time)
        
        # Calculate overall survival probability and count survivors
        current_survivors = 0
        current_total_probability = 0
        current_assignments = []
        
        for p_idx in range(num_patients):
            if p_idx == patient:
                final_prob = final_probability
            else:
                final_prob = patients[p_idx][min(time, len(patients[p_idx]) - 1)]
            
            current_total_probability += final_prob
            if final_prob > 50:
                current_survivors += 1
            
            # Record the assignment
            if p_idx == patient:
                current_assignments.append({'patient': p_idx, 'resource': resource_idx, 'time': time})
        
        # Check if this is the best solution so far
        if (current_survivors > best_survivors or
            (current_survivors == best_survivors and current_total_probability > best_total_survival_probability)):
            best_assignments = current_assignments
            best_survivors = current_survivors
            best_total_survival_probability = current_total_probability
    
    return {
        "assignments": best_assignments,
        "survivors": best_survivors,
        "total_survival_probability": best_total_survival_probability
    }

def main():
    input_data = json.load(sys.stdin)
    result = allocate_resources(
        input_data['patients'],
        input_data['resources'],
        input_data['responders'],
        input_data['total_time']
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()