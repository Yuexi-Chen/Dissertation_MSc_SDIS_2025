import json
import sys

def allocate_resources(patients, resources, responders, total_time):
    def calculate_probability(patient, resource, time):
        base_prob = patient[time] if time < len(patient) else 0
        return min(100, base_prob + resource['boost'])

    def dp_allocation():
        n = len(patients)
        m = len(resources)
        dp = [[[0 for _ in range(total_time + 1)] for _ in range(m + 1)] for _ in range(n + 1)]
        assignments = [[[[] for _ in range(total_time + 1)] for _ in range(m + 1)] for _ in range(n + 1)]

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                for t in range(1, total_time + 1):
                    dp[i][j][t] = dp[i - 1][j][t]
                    assignments[i][j][t] = assignments[i - 1][j][t].copy()

                    if t >= resources[j - 1]['time']:
                        prob = calculate_probability(patients[i - 1], resources[j - 1], t - resources[j - 1]['time'])
                        new_prob = dp[i - 1][j - 1][t - resources[j - 1]['time']] + prob
                        if new_prob > dp[i][j][t]:
                            dp[i][j][t] = new_prob
                            assignments[i][j][t] = assignments[i - 1][j - 1][t - resources[j - 1]['time']].copy()
                            assignments[i][j][t].append((i - 1, j - 1, t - resources[j - 1]['time']))

        return dp[n][m][total_time], assignments[n][m][total_time]

    total_prob, optimal_assignments = dp_allocation()

    final_assignments = []
    used_times = set()
    for patient, resource, time in optimal_assignments:
        if len([a for a in final_assignments if a['time'] <= time < a['time'] + resources[a['resource']]['time']]) < responders:
            final_assignments.append({
                'patient': patient,
                'resource': resource,
                'time': time
            })
            used_times.add(time)

    final_probabilities = [0] * len(patients)
    for assignment in final_assignments:
        patient = assignment['patient']
        resource = assignment['resource']
        time = assignment['time']
        final_probabilities[patient] = calculate_probability(patients[patient], resources[resource], time)

    survivors = sum(1 for prob in final_probabilities if prob > 50)
    total_survival_probability = sum(final_probabilities)

    return {
        'assignments': final_assignments,
        'survivors': survivors,
        'total_survival_probability': total_survival_probability
    }

def main():
    input_data = json.loads(sys.stdin.read())
    result = allocate_resources(
        input_data['patients'],
        input_data['resources'],
        input_data['responders'],
        input_data['total_time']
    )
    print(json.dumps(result))

if __name__ == "__main__":
    main()