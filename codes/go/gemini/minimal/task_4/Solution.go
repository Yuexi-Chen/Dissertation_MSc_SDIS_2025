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

	// dp[i][j] stores the maximum survival probability using the first i patients and j time units
	dp := make([][]float64, patientCount+1)
	for i := range dp {
		dp[i] = make([]float64, totalTime+1)
	}

	// Keep track of assignments made during DP calculation
	assignmentTracker := make([][][]map[string]interface{}, patientCount+1)
	for i := range assignmentTracker {
		assignmentTracker[i] = make([][]map[string]interface{}, totalTime+1)
		for j := range assignmentTracker[i] {
			assignmentTracker[i][j] = []map[string]interface{}{}
		}
	}

	// Iterate through each patient and consider all possible resource assignments
	for i := 1; i <= patientCount; i++ {
		for j := 0; j <= totalTime; j++ {
			dp[i][j] = dp[i-1][j] // Initialize with the probability without treating the current patient
			assignmentTracker[i][j] = assignmentTracker[i-1][j]

			// Consider all possible resource assignments for the current patient
			for r := 0; r < resourceCount; r++ {
				resourceTime := int(resources[r]["time"].(float64))
				resourceBoost := int(resources[r]["boost"].(float64))

				// Check if there is enough time to apply the resource
				if resourceTime <= j {
					// Calculate the survival probability with the resource applied
					treatmentTime := j - resourceTime
					baseProbability := float64(patients[i-1][treatmentTime])
					boostedProbability := math.Min(100.0, baseProbability+float64(resourceBoost))

					// Check if applying the resource increases the survival probability
					if dp[i-1][j-resourceTime]+boostedProbability > dp[i][j] {
						dp[i][j] = dp[i-1][j-resourceTime] + boostedProbability

						// Update the assignment tracker
						currentAssignments := make([]map[string]interface{}, len(assignmentTracker[i-1][j-resourceTime]))
						copy(currentAssignments, assignmentTracker[i-1][j-resourceTime])

						currentAssignments = append(currentAssignments, map[string]interface{}{
							"patient":  i - 1,
							"resource": r,
							"time":     treatmentTime,
						})
						assignmentTracker[i][j] = currentAssignments
					}
				}
			}
		}
	}

	// Extract the optimal assignments
	assignments = assignmentTracker[patientCount][totalTime]

	// Calculate the number of survivors and total survival probability
	survivorMap := make(map[int]bool)
	for _, assignment := range assignments {
		patientIndex := int(assignment["patient"].(int))
		resourceIndex := int(assignment["resource"].(int))
		treatmentTime := int(assignment["time"].(int))

		baseProbability := float64(patients[patientIndex][treatmentTime])
		resourceBoost := int(resources[resourceIndex]["boost"].(float64))
		boostedProbability := math.Min(100.0, baseProbability+float64(resourceBoost))

		totalSurvivalProbability += boostedProbability
		survivorMap[patientIndex] = true
	}

	survivors = len(survivorMap)

	result := map[string]interface{}{
		"assignments":               assignments,
		"survivors":                 survivors,
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

	patients := input["patients"].([][]int)
	resources := input["resources"].([]map[string]interface{})
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