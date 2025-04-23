import json

def allocate_resources(patients, resources, responders, total_time):
    """
    Allocates medical resources to patients to maximize survival probability.

    Args:
        patients (list): List of patient survival probability curves.
        resources (list): List of available medical resources.
        responders (int): Number of available responders.
        total_time (int): Maximum time available for treatments.

    Returns:
        dict: A dictionary containing the assignments, number of survivors, and total survival probability.
    """

    assignments = []
    patient_count = len(patients)
    resource_count = len(resources)

    # Initialize patient probabilities
    patient_probabilities = [[prob for prob in patient] for patient in patients]

    # Initialize responder availability
    responder_availability = [0] * responders

    # Iterate through possible treatment times
    for time in range(total_time):
        # Find available responders
        available_responder_indices = [i for i, available_at in enumerate(responder_availability) if available_at <= time]

        # If no responders are available, continue to the next time step
        if not available_responder_indices:
            continue

        # Calculate potential treatment outcomes
        potential_treatments = []
        for patient_index in range(patient_count):
            if patient_probabilities[patient_index][time] > 0:
                for resource_index in range(resource_count):
                    resource = resources[resource_index]
                    if time + resource['time'] <= total_time:
                        final_probability = min(100, patient_probabilities[patient_index][time] + resource['boost'])
                        potential_treatments.append({
                            'patient': patient_index,
                            'resource': resource_index,
                            'time': time,
                            'final_probability': final_probability
                        })

        # Sort potential treatments by final probability in descending order
        potential_treatments = sorted(potential_treatments, key=lambda x: x['final_probability'], reverse=True)

        # Assign resources to patients
        assigned_patients = set()
        assigned_resources = set()
        for treatment in potential_treatments:
            patient_index = treatment['patient']
            resource_index = treatment['resource']
            treatment_time = treatment['time']
            resource_time = resources[resource_index]['time']

            # Check if patient or resource has already been assigned
            if patient_index in assigned_patients or resource_index in assigned_resources:
                continue

            # Find an available responder
            responder_index = None
            for i in available_responder_indices:
                if responder_availability[i] <= treatment_time:
                    responder_index = i
                    break

            # If no responder is available, continue to the next treatment
            if responder_index is None:
                continue

            # Assign the resource to the patient
            assignments.append({
                'patient': patient_index,
                'resource': resource_index,
                'time': treatment_time
            })
            assigned_patients.add(patient_index)
            assigned_resources.add(resource_index)
            responder_availability[responder_index] = treatment_time + resource_time

            # Update patient probabilities
            final_probability = treatment['final_probability']
            for t in range(treatment_time, total_time):
                patient_probabilities[patient_index][t] = final_probability

    # Calculate number of survivors and total survival probability
    survivors = 0
    total_survival_probability = 0
    final_probabilities = [patient[total_time - 1] if total_time > 0 else patient[0] for patient in patient_probabilities]
    for prob in final_probabilities:
        if prob > 50:
            survivors += 1
        total_survival_probability += prob

    # Return the results
    return {
        'assignments': assignments,
        'survivors': survivors,
        'total_survival_probability': total_survival_probability
    }

if __name__ == "__main__":
    input_json = json.load(input())
    result = allocate_resources(
        patients=input_json['patients'],
        resources=input_json['resources'],
        responders=input_json['responders'],
        total_time=input_json['total_time']
    )
    print(json.dumps(result))