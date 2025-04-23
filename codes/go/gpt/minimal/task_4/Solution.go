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

	for i := 0; i < len(patients); i++ {
		for j := 0; j < len(resources); j++ {
			resourceTime := int(resources[j]["time"].(float64))
			boost := int(resources[j]["boost"].(float64))
			if resourceTime <= totalTime {
				survivalProbability := patients[i][resourceTime-1] + boost
				if survivalProbability > 100 {
					survivalProbability = 100
				}
				if survivalProbability > 0 && responders > 0 {
					assignments = append(assignments, map[string]int{"patient": i, "resource": j, "time": resourceTime - 1})
					survivors++
					totalSurvivalProbability += survivalProbability
					responders--
					break
				}
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
	var input struct {
		Patients   [][]int               `json:"patients"`
		Resources  []map[string]interface{} `json:"resources"`
		Responders int                  `json:"responders"`
		TotalTime  int                  `json:"total_time"`
	}

	json.NewDecoder(os.Stdin).Decode(&input)

	result := allocateResources(input.Patients, input.Resources, input.Responders, input.TotalTime)

	output, _ := json.Marshal(result)
	fmt.Println(string(output))
}