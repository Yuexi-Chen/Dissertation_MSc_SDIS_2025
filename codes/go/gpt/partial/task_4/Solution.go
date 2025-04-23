package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func allocateResources(patients [][]int, resources []map[string]interface{}, responders int, totalTime int) map[string]interface{} {
	assignments := []map[string]int{}
	survivors := 0
	totalSurvivalProbability := 0

	// Simulate a simple greedy allocation strategy
	availableResponders := make([]int, totalTime)
	resourceUsage := make([]bool, len(resources))
	for t := 0; t < totalTime; t++ {
		availableResponders[t] = responders
	}

	for time := 0; time < totalTime; time++ {
		for i, patient := range patients {
			if time < len(patient) && availableResponders[time] > 0 {
				bestResourceIdx := -1
				bestProbability := 0
				for j, resource := range resources {
					if resourceUsage[j] {
						continue
					}
					resourceTime := int(resource["time"].(float64))
					boost := int(resource["boost"].(float64))
					if time+resourceTime < len(patient) {
						newProbability := patient[time+resourceTime] + boost
						if newProbability > 100 {
							newProbability = 100
						}
						if newProbability > bestProbability {
							bestProbability = newProbability
							bestResourceIdx = j
						}
					}
				}
				if bestResourceIdx != -1 {
					availableResponders[time]--
					resourceUsage[bestResourceIdx] = true
					assignments = append(assignments, map[string]int{"patient": i, "resource": bestResourceIdx, "time": time})
					if bestProbability > 50 {
						survivors++
					}
					totalSurvivalProbability += bestProbability
				}
			}
		}
	}

	return map[string]interface{}{
		"assignments":             assignments,
		"survivors":               survivors,
		"total_survival_probability": totalSurvivalProbability,
	}
}

func main() {
	var input map[string]interface{}
	json.NewDecoder(os.Stdin).Decode(&input)

	patients := input["patients"].([]interface{})
	convertedPatients := make([][]int, len(patients))
	for i, p := range patients {
		patient := p.([]interface{})
		convertedPatients[i] = make([]int, len(patient))
		for j, prob := range patient {
			convertedPatients[i][j] = int(prob.(float64))
		}
	}

	resources := input["resources"].([]interface{})
	convertedResources := make([]map[string]interface{}, len(resources))
	for i, r := range resources {
		convertedResources[i] = r.(map[string]interface{})
	}

	responders := int(input["responders"].(float64))
	totalTime := int(input["total_time"].(float64))

	result := allocateResources(convertedPatients, convertedResources, responders, totalTime)
	output, _ := json.Marshal(result)
	fmt.Println(string(output))
}