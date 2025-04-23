package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func allocateResources(patients [][]int, resources []map[string]interface{}, responders int, totalTime int) map[string]interface{} {
	assignments := []map[string]interface{}{}
	survivors := 0
	totalSurvivalProbability := 0.0

	dp := make([][][]float64, totalTime+1)
	for t := range dp {
		dp[t] = make([][]float64, len(patients))
		for p := range dp[t] {
			dp[t][p] = make([]float64, responders+1)
		}
	}

	for t := 1; t <= totalTime; t++ {
		for p := 0; p < len(patients); p++ {
			for r := 1; r <= responders; r++ {
				dp[t][p][r] = dp[t-1][p][r]
				if t < len(patients[p]) {
					dp[t][p][r] = max(dp[t][p][r], float64(patients[p][t]))
				}
				for _, resource := range resources {
					resourceTime := int(resource["time"].(float64))
					resourceBoost := resource["boost"].(float64)
					if t >= resourceTime {
						prevProb := dp[t-resourceTime][p][r-1]
						if prevProb > 0 {
							boostedProb := min(prevProb+resourceBoost, 100)
							if boostedProb > dp[t][p][r] {
								dp[t][p][r] = boostedProb
							}
						}
					}
				}
			}
		}
	}

	assigned := make([]bool, len(patients))
	for t := totalTime; t > 0; t-- {
		for r := responders; r > 0; r-- {
			for p := 0; p < len(patients); p++ {
				if !assigned[p] && dp[t][p][r] > dp[t][p][r-1] {
					for _, resource := range resources {
						resourceTime := int(resource["time"].(float64))
						resourceBoost := resource["boost"].(float64)
						if t >= resourceTime {
							prevProb := dp[t-resourceTime][p][r-1]
							boostedProb := min(prevProb+resourceBoost, 100)
							if boostedProb == dp[t][p][r] {
								assignments = append(assignments, map[string]interface{}{
									"patient":  p,
									"resource": resource,
									"time":     t - resourceTime,
								})
								assigned[p] = true
								break
							}
						}
					}
					break
				}
			}
		}
	}

	for p, prob := range dp[totalTime] {
		finalProb := prob[responders]
		if finalProb > 50 {
			survivors++
		}
		totalSurvivalProbability += finalProb
	}

	return map[string]interface{}{
		"assignments":               assignments,
		"survivors":                 survivors,
		"total_survival_probability": totalSurvivalProbability,
	}
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
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
	patientsProbabilities := make([][]int, len(patients))
	for i, patient := range patients {
		probabilities := patient.([]interface{})
		patientsProbabilities[i] = make([]int, len(probabilities))
		for j, prob := range probabilities {
			patientsProbabilities[i][j] = int(prob.(float64))
		}
	}

	resources := input["resources"].([]interface{})
	resourcesMaps := make([]map[string]interface{}, len(resources))
	for i, resource := range resources {
		resourcesMaps[i] = resource.(map[string]interface{})
	}

	responders := int(input["responders"].(float64))
	totalTime := int(input["total_time"].(float64))

	result := allocateResources(patientsProbabilities, resourcesMaps, responders, totalTime)

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	err = encoder.Encode(result)
	if err != nil {
		fmt.Println("Error encoding result:", err)
	}
}