package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
)

func allocateResources(patients [][]int, resources []map[string]interface{}, responders int, totalTime int) map[string]interface{} {
	type Assignment struct {
		Patient int `json:"patient"`
		Resource int `json:"resource"`
		Time int `json:"time"`
	}

	assignments := []Assignment{}
	survivors := 0
	totalSurvivalProbability := 0.0

	// Dynamic programming table
	dp := make([][][]float64, len(patients))
	for i := range dp {
		dp[i] = make([][]float64, len(resources))
		for j := range dp[i] {
			dp[i][j] = make([]float64, totalTime+1)
			for k := range dp[i][j] {
				dp[i][j][k] = -1
			}
		}
	}

	// Helper function to calculate probability after applying a resource
	calcProb := func(patient, resource, time int) float64 {
		if time >= len(patients[patient]) {
			return 0
		}
		baseProb := float64(patients[patient][time])
		boost := resources[resource]["boost"].(float64)
		return math.Min(100, baseProb + boost)
	}

	// Recursive function to fill dp table
	var fillDP func(patient, resource, time int) float64
	fillDP = func(patient, resource, time int) float64 {
		if patient >= len(patients) || time > totalTime {
			return 0
		}
		if dp[patient][resource][time] != -1 {
			return dp[patient][resource][time]
		}

		// Don't apply this resource
		maxProb := fillDP(patient+1, 0, time)

		// Apply this resource if possible
		if time + int(resources[resource]["time"].(float64)) <= totalTime {
			prob := calcProb(patient, resource, time)
			prob += fillDP(patient+1, 0, time+int(resources[resource]["time"].(float64)))
			maxProb = math.Max(maxProb, prob)
		}

		dp[patient][resource][time] = maxProb
		return maxProb
	}

	// Fill the dp table
	fillDP(0, 0, 0)

	// Backtrack to find assignments
	currentTime := 0
	for patient := 0; patient < len(patients); patient++ {
		bestResource := -1
		bestTime := -1
		maxProb := 0.0

		for resource := 0; resource < len(resources); resource++ {
			for time := currentTime; time <= totalTime-int(resources[resource]["time"].(float64)); time++ {
				prob := calcProb(patient, resource, time)
				if prob > maxProb {
					maxProb = prob
					bestResource = resource
					bestTime = time
				}
			}
		}

		if bestResource != -1 {
			assignments = append(assignments, Assignment{
				Patient:  patient,
				Resource: bestResource,
				Time:     bestTime,
			})
			currentTime = bestTime + int(resources[bestResource]["time"].(float64))
			totalSurvivalProbability += maxProb
			if maxProb > 50 {
				survivors++
			}
		}
	}

	return map[string]interface{}{
		"assignments":               assignments,
		"survivors":                 survivors,
		"total_survival_probability": totalSurvivalProbability,
	}
}

func main() {
	var input map[string]interface{}
	decoder := json.NewDecoder(os.Stdin)
	err := decoder.Decode(&input)
	if err != nil {
		fmt.Println("Error decoding input:", err)
		return
	}

	patients := input["patients"].([]interface{})
	patientsList := make([][]int, len(patients))
	for i, patient := range patients {
		patientProbs := patient.([]interface{})
		patientsList[i] = make([]int, len(patientProbs))
		for j, prob := range patientProbs {
			patientsList[i][j] = int(prob.(float64))
		}
	}

	resources := input["resources"].([]interface{})
	resourcesList := make([]map[string]interface{}, len(resources))
	for i, resource := range resources {
		resourcesList[i] = resource.(map[string]interface{})
	}

	responders := int(input["responders"].(float64))
	totalTime := int(input["total_time"].(float64))

	result := allocateResources(patientsList, resourcesList, responders, totalTime)

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	err = encoder.Encode(result)
	if err != nil {
		fmt.Println("Error encoding output:", err)
	}
}