def allocate_resources(patients, resources, responders, total_time):
    import heapq

    def get_final_probability(probability, boost):
        return min(probability + boost, 100)

    num_patients = len(patients)
    num_resources = len(resources)
    assignments = []
    available_responders = [0] * responders  # array to track responder availability times
    max_heap = []

    for patient_index in range(num_patients):
        for resource_index in range(num_resources):
            resource_time = resources[resource_index]['time']
            boost = resources[resource_index]['boost']

            # Calculate probabilities for each start time
            for start_time in range(total_time - resource_time + 1):
                if patients[patient_index][start_time] > 0:
                    final_probability = get_final_probability(patients[patient_index][start_time], boost)
                    heapq.heappush(max_heap, (-final_probability, start_time, patient_index, resource_index))

    scheduled = set()
    total_survival_probability = 0

    while max_heap and len(assignments) < responders:
        neg_probability, start_time, patient_index, resource_index = heapq.heappop(max_heap)
        resource_time = resources[resource_index]['time']
        boost = resources[resource_index]['boost']
        final_probability = -neg_probability

        # Check if this patient has already been assigned a resource
        if patient_index in scheduled:
            continue

        # Find a responder that can take this task
        responder_assigned = False
        for i in range(responders):
            if available_responders[i] <= start_time:
                available_responders[i] = start_time + resource_time
                assignments.append({"patient": patient_index, "resource": resource_index, "time": start_time})
                total_survival_probability += final_probability
                scheduled.add(patient_index)
                responder_assigned = True
                break
        
        if not responder_assigned:
            continue

    survivors = len([p for p in assignments if patients[p['patient']][p['time']] + resources[p['resource']]['boost'] > 50])

    return {
        "assignments": assignments,
        "survivors": survivors,
        "total_survival_probability": total_survival_probability
    }

def main():
    import sys
    import json

    input_data = json.load(sys.stdin)
    result = allocate_resources(
        input_data['patients'],
        input_data['resources'],
        input_data['responders'],
        input_data['total_time']
    )
    print(json.dumps(result))

if __name__ == "__main__":
    main()