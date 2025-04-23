import json

def allocate_resources(patients, resources, responders, total_time):
    assignments = []
    survivors = 0
    total_survival_probability = 0

    import heapq

    def calculate_survival_probability(patient_probabilities, resource, start_time):
        """Calculates survival probability after applying a resource at a given time."""
        if start_time >= len(patient_probabilities):
            return 0.0  # Patient has already passed away

        base_probability = patient_probabilities[start_time] / 100.0
        boosted_probability = min(1.0, base_probability + (resource['boost'] / 100.0))
        return boosted_probability

    def find_best_assignments(patients, resources, responders, total_time):
        """Finds the best possible resource assignments to maximize survival."""

        best_assignments = []
        max_survival_prob = 0

        def explore_assignments(current_assignments, current_survival_prob, available_responders):
            nonlocal best_assignments, max_survival_prob
            
            # Base case: all patients have been considered
            if len(current_assignments) == len(patients):
                if current_survival_prob > max_survival_prob:
                    max_survival_prob = current_survival_prob
                    best_assignments = current_assignments[:]
                return

            patient_index = len(current_assignments)
            patient_probabilities = patients[patient_index]

            # Option 1: Don't assign any resource to the current patient
            explore_assignments(current_assignments + [None], current_survival_prob, available_responders)

            # Option 2: Try assigning each resource at each possible time
            for resource_index, resource in enumerate(resources):
                for start_time in range(total_time - resource['time'] + 1):
                    
                    # Check if responders are available during the entire treatment time
                    responder_needed = True
                    for t in range(start_time, start_time + resource['time']):
                        if available_responders[t] == 0:
                            responder_needed = False
                            break
                    
                    if responder_needed:
                        # Apply the resource
                        new_available_responders = available_responders[:]
                        for t in range(start_time, start_time + resource['time']):
                            new_available_responders[t] -= 1

                        survival_prob = calculate_survival_probability(patient_probabilities, resource, start_time)
                        
                        explore_assignments(current_assignments + [{"patient": patient_index, "resource": resource_index, "time": start_time}],
                                            current_survival_prob + survival_prob,
                                            new_available_responders)

        # Initialize available responders at each time step
        available_responders = [responders] * total_time
        explore_assignments([], 0, available_responders)

        return best_assignments, max_survival_prob

    # Find the best assignments
    best_assignments, max_survival_prob = find_best_assignments(patients, resources, responders, total_time)

    # Process the assignments
    if best_assignments:
        survivors = 0
        total_survival_probability = 0
        final_assignments = []
        
        for assignment in best_assignments:
            if assignment:
                patient_index = assignment['patient']
                resource_index = assignment['resource']
                start_time = assignment['time']
                
                final_assignments.append(assignment)
                
                survival_prob = calculate_survival_probability(patients[patient_index], resources[resource_index], start_time)
                
                if survival_prob > 0:
                    survivors += 1
                total_survival_probability += survival_prob * 100
        
        assignments = final_assignments
    
    return {"assignments": assignments, "survivors": survivors, "total_survival_probability": total_survival_probability}

if __name__ == "__main__":
    import sys
    input_str = sys.stdin.read()
    input_data = json.loads(input_str)
    result = allocate_resources(input_data["patients"], input_data["resources"], input_data["responders"], input_data["total_time"])
    print(json.dumps(result))