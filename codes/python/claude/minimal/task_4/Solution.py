import json
import sys

def allocate_resources(patients, resources, responders, total_time):
    def calculate_survival_probability(patient, resource, start_time):
        end_time = start_time + resource['time']
        if end_time >= len(patient):
            return 0
        return min(100, patient[end_time] + resource['boost'])

    dp = [[[0 for _ in range(responders + 1)] for _ in range(total_time + 1)] for _ in range(len(patients) + 1)]
    assignments = []

    for p in range(1, len(patients) + 1):
        for t in range(total_time + 1):
            for r in range(responders + 1):
                dp[p][t][r] = dp[p-1][t][r]
                for resource in resources:
                    if t >= resource['time'] and r > 0:
                        prob = calculate_survival_probability(patients[p-1], resource, t - resource['time'])
                        new_value = dp[p-1][t - resource['time']][r-1] + prob
                        if new_value > dp[p][t][r]:
                            dp[p][t][r] = new_value

    total_survival_probability = dp[len(patients)][total_time][responders]
    survivors = sum(1 for prob in dp[len(patients)][total_time] if prob > 0)

    p, t, r = len(patients), total_time, responders
    while p > 0 and t > 0 and r > 0:
        if dp[p][t][r] != dp[p-1][t][r]:
            for resource_idx, resource in enumerate(resources):
                if t >= resource['time']:
                    prob = calculate_survival_probability(patients[p-1], resource, t - resource['time'])
                    if dp[p][t][r] == dp[p-1][t - resource['time']][r-1] + prob:
                        assignments.append({
                            "patient": p-1,
                            "resource": resource_idx,
                            "time": t - resource['time']
                        })
                        t -= resource['time']
                        r -= 1
                        break
        p -= 1

    assignments.sort(key=lambda x: x['time'])
    return {
        "assignments": assignments,
        "survivors": survivors,
        "total_survival_probability": total_survival_probability
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