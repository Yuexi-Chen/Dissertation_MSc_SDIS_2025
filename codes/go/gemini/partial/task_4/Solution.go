package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
)

func allocateResources(patients [][]int, resources []map[string]interface{}, responders int, totalTime int) map[string]interface{} {
	assignments := []map[string]interface{}{}
	survivors := 0
	totalSurvivalProbability := 0.0

	patientCount := len(patients)
	resourceCount := len(resources)

	// dp[i][t] stores the maximum total survival probability achievable by considering
	// the first i patients and using time up to t.
	dp := make([][]float64, patientCount+1)
	for i := range dp {
		dp[i] = make([]float64, totalTime+1)
	}

	// keep track of the assignments made for each dp state.
	assignmentTracker := make([][][]map[string]interface{}, patientCount+1)
	for i := range assignmentTracker {
		assignmentTracker[i] = make([][]map[string]interface{}, totalTime+1)
		for j := range assignmentTracker[i] {
			assignmentTracker[i][j] = []map[string]interface{}{}
		}
	}

	for i := 1; i <= patientCount; i++ {
		for t := 0; t <= totalTime; t++ {
			dp[i][t] = dp[i-1][t]
			assignmentTracker[i][t] = assignmentTracker[i-1][t]

			for r := 0; r < resourceCount; r++ {
				resource := resources[r]
				resourceTime := int(resource["time"].(float64))
				resourceBoost := resource["boost"].(float64)

				if resourceTime <= t {
					currentTime := 0
					survivalProbability := float64(patients[i-1][currentTime]) / 100.0

					boostedProbability := math.Min(1.0, survivalProbability+resourceBoost/100.0)

					if dp[i-1][t-resourceTime]+boostedProbability > dp[i][t] {
						dp[i][t] = dp[i-1][t-resourceTime] + boostedProbability

						newAssignments := make([]map[string]interface{}, len(assignmentTracker[i-1][t-resourceTime]))
						copy(newAssignments, assignmentTracker[i-1][t-resourceTime])

						newAssignments = append(newAssignments, map[string]interface{}{
							"patient":  i - 1,
							"resource": r,
							"time":     0, // Assuming always starting at time 0 for now
						})

						assignmentTracker[i][t] = newAssignments
					}
				}
			}
		}
	}

	assignments = assignmentTracker[patientCount][totalTime]

	finalProbabilities := make([]float64, patientCount)
	for _, assignment := range assignments {
		patientIndex := int(assignment["patient"].(float64))
		resourceIndex := int(assignment["resource"].(float64))
		resource := resources[resourceIndex]
		resourceBoost := resource["boost"].(float64)

		currentTime := 0
		survivalProbability := float64(patients[patientIndex][currentTime]) / 100.0
		boostedProbability := math.Min(1.0, survivalProbability+resourceBoost/100.0)

		finalProbabilities[patientIndex] = boostedProbability
	}

	for i := 0; i < patientCount; i++ {
		if finalProbabilities[i] > 0.5 {
			survivors++
		}
		totalSurvivalProbability += finalProbabilities[i] * 100.0
	}

	result := map[string]interface{}{
		"assignments":                assignments,
		"survivors":                  survivors,
		"total_survival_probability": totalSurvivalProbability,
	}

	return result
}

func main() {
	var input map[string]interface{}
	decoder := json.NewDecoder(os.Stdin)
	err := decoder.Decode(&input)
	if err != nil {
		fmt.Println("Error decoding JSON:", err)
		return
	}

	patientsInterface := input["patients"].([]interface{})
	patients := make([][]int, len(patientsInterface))
	for i, patientInterface := range patientsInterface {
		patient := patientInterface.([]interface{})
		patients[i] = make([]int, len(patient))
		for j, probInterface := range patient {
			patients[i][j] = int(probInterface.(float64))
		}
	}

	resourcesInterface := input["resources"].([]interface{})
	resources := make([]map[string]interface{}, len(resourcesInterface))
	for i, resourceInterface := range resourcesInterface {
		resources[i] = resourceInterface.(map[string]interface{})
	}

	responders := int(input["responders"].(float64))
	totalTime := int(input["total_time"].(float64))

	result := allocateResources(patients, resources, responders, totalTime)

	jsonResult, err := json.Marshal(result)
	if err != nil {
		fmt.Println("Error encoding JSON:", err)
		return
	}

	fmt.Println(string(jsonResult))
}