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
				for _, resource := range resources {
					resourceTime := int(resource["time"].(float64))
					resourceBoost := int(resource["boost"].(float64))
					if t >= resourceTime {
						prob := float64(patients[p][min(t-resourceTime, len(patients[p])-1)]) + float64(resourceBoost)
						prob = min(prob, 100)
						dp[t][p][r] = math.Max(dp[t][p][r], dp[t-resourceTime][p][r-1]+prob)
					}
				}
			}
		}
	}

	allocated := make([]bool, len(patients))
	responderAvailable := make([]int, responders)

	var backtrack func(t, r int)
	backtrack = func(t, r int) {
		if t == 0 || r == 0 {
			return
		}
		for p := 0; p < len(patients); p++ {
			if allocated[p] {
				continue
			}
			for _, resource := range resources {
				resourceTime := int(resource["time"].(float64))
				resourceBoost := int(resource["boost"].(float64))
				if t >= resourceTime && r > 0 {
					prob := float64(patients[p][min(t-resourceTime, len(patients[p])-1)]) + float64(resourceBoost)
					prob = min(prob, 100)
					if math.Abs(dp[t][p][r]-dp[t-resourceTime][p][r-1]-prob) < 1e-9 {
						allocated[p] = true
						assignments = append(assignments, map[string]interface{}{
							"patient":  p,
							"resource": resource["time"],
							"time":     t - resourceTime,
						})
						responderAvailable[r-1] = t
						backtrack(t-resourceTime, r-1)
						return
					}
				}
			}
		}
		backtrack(t-1, r)
	}

	backtrack(totalTime, responders)

	for p, patient := range patients {
		finalProb := patient[min(totalTime, len(patient)-1)]
		for _, assignment := range assignments {
			if assignment["patient"].(int) == p {
				resourceTime := int(assignment["resource"].(float64))
				resourceBoost := 0
				for _, resource := range resources {
					if resource["time"] == assignment["resource"] {
						resourceBoost = int(resource["boost"].(float64))
						break
					}
				}
				finalProb = min(finalProb+resourceBoost, 100)
			}
		}
		if finalProb >= 50 {
			survivors++
		}
		totalSurvivalProbability += float64(finalProb)
	}

	return map[string]interface{}{
		"assignments":               assignments,
		"survivors":                 survivors,
		"total_survival_probability": totalSurvivalProbability,
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func main() {
	var input map[string]interface{}
	err := json.NewDecoder(os.Stdin).Decode(&input)
	if err != nil {
		fmt.Println("Error reading input:", err)
		return
	}

	patients := input["patients"].([]interface{})
	var patientsInt [][]int
	for _, p := range patients {
		pInt := make([]int, len(p.([]interface{})))
		for i, v := range p.([]interface{}) {
			pInt[i] = int(v.(float64))
		}
		patientsInt = append(patientsInt, pInt)
	}

	resources := input["resources"].([]interface{})
	var resourcesMaps []map[string]interface{}
	for _, r := range resources {
		resourcesMaps = append(resourcesMaps, r.(map[string]interface{}))
	}

	responders := int(input["responders"].(float64))
	totalTime := int(input["total_time"].(float64))

	result := allocateResources(patientsInt, resourcesMaps, responders, totalTime)

	json.NewEncoder(os.Stdout).Encode(result)
}