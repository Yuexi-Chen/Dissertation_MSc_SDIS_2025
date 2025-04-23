import json
import sys

def allocate_resources(patients, resources, responders, total_time):
    def apply_resource(patient, resource, time):
        start_prob = patient[time]
        end_prob = min(100, start_prob + resource['boost'])
        return end_prob

    def calculate_probabilities():
        probs = []
        for patient in patients:
            patient_probs = []
            for t in range(total_time):
                resource_probs = []
                for resource in resources:
                    if t + resource['time'] <= total_time:
                        prob = apply_resource(patient, resource, t)
                        resource_probs.append((prob, resource, t))
                patient_probs.append(resource_probs)
            probs.append(patient_probs)
        return probs

    def optimize_allocation(probs):
        dp = [[[0 for _ in range(responders + 1)] for _ in range(total_time + 1)] for _ in range(len(patients) + 1)]
        assignments = [[[[] for _ in range(responders + 1)] for _ in range(total_time + 1)] for _ in range(len(patients) + 1)]

        for p in range(1, len(patients) + 1):
            for t in range(total_time + 1):
                for r in range(responders + 1):
                    dp[p][t][r] = dp[p-1][t][r]
                    assignments[p][t][r] = assignments[p-1][t][r].copy()

                    for prob, resource, start_time in probs[p-1][t]:
                        if start_time + resource['time'] <= t and r > 0:
                            new_prob = dp[p-1][start_time][r-1] + prob
                            if new_prob > dp[p][t][r]:
                                dp[p][t][r] = new_prob
                                assignments[p][t][r] = assignments[p-1][start_time][r-1].copy()
                                assignments[p][t][r].append((p-1, resource, start_time))

        return assignments[len(patients)][total_time][responders]

    probs = calculate_probabilities()
    optimal_assignments = optimize_allocation(probs)

    final_probabilities = [patients[i][0] for i in range(len(patients))]
    for patient, resource, time in optimal_assignments:
        final_probabilities[patient] = apply_resource(patients[patient], resource, time)

    survivors = sum(1 for prob in final_probabilities if prob > 50)
    total_survival_probability = sum(final_probabilities)

    return {
        "assignments": [{"patient": patient, "resource": resources.index(resource), "time": time}
                        for patient, resource, time in optimal_assignments],
        "survivors": survivors,
        "total_survival_probability": total_survival_probability
    }

def main():
    input_data = json.loads(sys.stdin.read())
    result = allocate_resources(
        input_data["patients"],
        input_data["resources"],
        input_data["responders"],
        input_data["total_time"]
    )
    print(json.dumps(result))

if __name__ == "__main__":
    main()