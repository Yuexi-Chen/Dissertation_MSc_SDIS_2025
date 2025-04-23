package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Resource struct {
	Time  int `json:"time"`
	Boost int `json:"boost"`
}

type Assignment struct {
	Patient  int `json:"patient"`
	Resource int `json:"resource"`
	Time     int `json:"time"`
}

func allocateResources(patients [][]int, resources []map[string]interface{}, responders int, totalTime int) map[string]interface{} {
	n := len(patients)
	m := len(resources)

	// Convert resource interfaces to Resource structs
	parsedResources := make([]Resource, m)
	for i, res := range resources {
		parsedResources[i] = Resource{
			Time:  int(res["time"].(float64)),
			Boost: int(res["boost"].(float64)),
		}
	}

	assignments := []Assignment{}
	survivors := 0
	totalSurvivalProbability := 0

	// Use a greedy approach to assign resources to maximize survival probability
	for t := 0; t < totalTime; t++ {
		availableResponders := responders
		for p := 0; p < n; p++ {
			if availableResponders <= 0 {
				break
			}
			maxIncrease := -1
			bestResource := -1
			bestTime := -1

			for r := 0; r < m; r++ {
				resource := parsedResources[r]
				if resource.Time > totalTime-t || patients[p][t] == 0 {
					continue
				}

				treatmentTime := t + resource.Time
				if treatmentTime < len(patients[p]) {
					currentProbability := patients[p][treatmentTime]
					newProbability := currentProbability + resource.Boost
					if newProbability > 100 {
						newProbability = 100
					}

					increase := newProbability - currentProbability
					if increase > maxIncrease {
						maxIncrease = increase
						bestResource = r
						bestTime = t
					}
				}
			}

			if bestResource != -1 {
				availableResponders--
				assignments = append(assignments, Assignment{
					Patient:  p,
					Resource: bestResource,
					Time:     bestTime,
				})
				// Apply the best resource to this patient
				resource := parsedResources[bestResource]
				treatmentTime := bestTime + resource.Time
				newProbability := patients[p][treatmentTime] + resource.Boost
				if newProbability > 100 {
					newProbability = 100
				}
				patients[p][treatmentTime] = newProbability
			}
		}
	}

	for _, patient := range patients {
		finalProbability := patient[len(patient)-1]
		totalSurvivalProbability += finalProbability
		if finalProbability > 50 {
			survivors++
		}
	}

	return map[string]interface{}{
		"assignments":              assignments,
		"survivors":                survivors,
		"total_survival_probability": totalSurvivalProbability,
	}
}

func main() {
	var input struct {
		Patients  [][]int            `json:"patients"`
		Resources []map[string]interface{} `json:"resources"`
		Responders int               `json:"responders"`
		TotalTime int                `json:"total_time"`
	}

	decoder := json.NewDecoder(os.Stdin)
	if err := decoder.Decode(&input); err != nil {
		fmt.Fprintln(os.Stderr, "Error reading input:", err)
		return
	}

	result := allocateResources(input.Patients, input.Resources, input.Responders, input.TotalTime)

	output, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		fmt.Fprintln(os.Stderr, "Error marshaling output:", err)
		return
	}

	fmt.Println(string(output))
}