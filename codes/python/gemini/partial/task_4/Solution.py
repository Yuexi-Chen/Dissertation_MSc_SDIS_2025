def allocate_resources(patients, resources, responders, total_time):
    """
    Allocates medical resources to patients to maximize the number of survivors.

    Args:
        patients (list): A list of patient survival probability curves.
        resources (list): A list of medical resources with time and boost.
        responders (int): The number of available responders.
        total_time (int): The total time available for treatments.

    Returns:
        dict: A dictionary containing the assignments, number of survivors, and total survival probability.
    """

    assignments = []
    patient_probabilities = [p[:] for p in patients]  # Copy to avoid modifying input
    responder_availability = [0] * responders  # Track when each responder is available
    patient_treated = [False] * len(patients)  # Track which patients have been treated

    # Iterate through time slots
    for t in range(total_time):
        # Find the best possible treatment for each responder
        best_treatment_for_responder = [None] * responders
        best_probability_increase = [0] * responders

        for responder_id in range(responders):
            if responder_availability[responder_id] <= t:  # Responder is available
                for patient_id, patient_curve in enumerate(patient_probabilities):
                    if not patient_treated[patient_id]: # Only consider patients that haven't been treated
                        for resource_id, resource in enumerate(resources):
                            if t + resource["time"] <= total_time:
                                # Calculate the potential probability increase
                                current_probability = patient_curve[min(t, len(patient_curve) - 1)]
                                new_probability = min(100, current_probability + resource["boost"])
                                probability_increase = new_probability - current_probability

                                # Update best treatment if it improves survival probability
                                if probability_increase > best_probability_increase[responder_id]:
                                    best_probability_increase[responder_id] = probability_increase
                                    best_treatment_for_responder[responder_id] = {
                                        "patient": patient_id,
                                        "resource": resource_id,
                                        "time": t,
                                        "probability": new_probability
                                    }

        # Assign the best treatments, prioritizing those that maximize probability increase
        treatment_indices = sorted(range(responders), key=lambda k: best_probability_increase[k], reverse=True)

        for treatment_index in treatment_indices:
            treatment = best_treatment_for_responder[treatment_index]
            if treatment:
                patient_id = treatment["patient"]
                resource_id = treatment["resource"]
                start_time = treatment["time"]
                resource_time = resources[resource_id]["time"]

                assignments.append({
                    "patient": patient_id,
                    "resource": resource_id,
                    "time": start_time
                })

                # Update responder availability
                responder_availability[treatment_index] = start_time + resource_time
                patient_probabilities[patient_id] = [treatment["probability"]] * len(patient_probabilities[patient_id])
                patient_treated[patient_id] = True

    # Calculate the number of survivors and total survival probability
    survivors = 0
    total_survival_probability = 0

    for prob in patient_probabilities:
        final_probability = prob[0]
        if final_probability > 50:
            survivors += 1
        total_survival_probability += final_probability

    return {
        "assignments": assignments,
        "survivors": survivors,
        "total_survival_probability": total_survival_probability
    }

if __name__ == "__main__":
    import json
    import sys

    input_data = json.loads(sys.stdin.read())
    result = allocate_resources(input_data["patients"], input_data["resources"], input_data["responders"], input_data["total_time"])
    print(json.dumps(result))