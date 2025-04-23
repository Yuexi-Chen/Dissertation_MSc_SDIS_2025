package main

import (
	"encoding/json"
	"fmt"
	"sort"
)

func allocateResources(patients [][]int, resources []map[string]interface{}, responders int, totalTime int) map[string]interface{} {
	assignments := []map[string]interface{}{}
	survivors := 0
	totalSurvivalProbability := 0.0

	patientCount := len(patients)
	resourceCount := len(resources)

	patientProbabilities := make([][]float64, patientCount)
	for i := range patients {
		patientProbabilities[i] = make([]float64, len(patients[i]))
		for j := range patients[i] {
			patientProbabilities[i][j] = float64(patients[i][j]) / 100.0
		}
	}

	resourceBoosts := make([]float64, resourceCount)
	resourceTimes := make([]int, resourceCount)

	for i := range resources {
		resourceBoosts[i] = float64(resources[i]["boost"].(int)) / 100.0
		resourceTimes[i] = resources[i]["time"].(int)
	}

	// Initialize responder availability
	responderAvailability := make([]int, responders) // Time when each responder is available

	// Possible assignments: patient, resource, time
	type Assignment struct {
		Patient  int
		Resource int
		Time     int
		Probability float64
	}

	possibleAssignments := []Assignment{}

	// Find all possible assignments
	for p := 0; p < patientCount; p++ {
		for r := 0; r < resourceCount; r++ {
			for t := 0; t < len(patientProbabilities[p]) && t+resourceTimes[r] <= totalTime; t++ {
				initialProbability := patientProbabilities[p][t]
				if initialProbability == 0 {
					continue
				}
				finalProbability := initialProbability + resourceBoosts[r]
				if finalProbability > 1.0 {
					finalProbability = 1.0
				}

				possibleAssignments = append(possibleAssignments, Assignment{
					Patient:  p,
					Resource: r,
					Time:     t,
					Probability: finalProbability,
				})
			}
		}
	}

	// Sort assignments by probability gain (higher gain first)
	sort.Slice(possibleAssignments, func(i, j int) bool {
		return possibleAssignments[i].Probability > possibleAssignments[j].Probability
	})

	assigned := make([]bool, patientCount)

	// Iterate over possible assignments and assign resources
	for _, assignment := range possibleAssignments {
		patient := assignment.Patient
		resource := assignment.Resource
		time := assignment.Time

		// Check if patient is already assigned
		if assigned[patient] {
			continue
		}
		
		// Find an available responder
		responderIndex := -1
		for i := range responderAvailability {
			if responderAvailability[i] <= time {
				responderIndex = i
				break
			}
		}

		// No responder available
		if responderIndex == -1 {
			continue
		}

		// Assign the resource
		assignments = append(assignments, map[string]interface{}{
			"patient":  patient,
			"resource": resource,
			"time":     time,
		})

		// Update responder availability
		responderAvailability[responderIndex] = time + resourceTimes[resource]

		// Update patient status
		assigned[patient] = true
	}

	finalProbabilities := make([]float64, patientCount)
	for i := range patientProbabilities {
		finalProbabilities[i] = patientProbabilities[i][len(patientProbabilities[i])-1]
	}
	for _, assignment := range assignments {
		patient := assignment["patient"].(int)
		resource := assignment["resource"].(int)
		time := assignment["time"].(int)

		initialProbability := patientProbabilities[patient][time]
		finalProbability := initialProbability + resourceBoosts[resource]
		if finalProbability > 1.0 {
			finalProbability = 1.0
		}
		finalProbabilities[patient] = finalProbability
	}

	// Calculate survivors and total survival probability
	for i := range finalProbabilities {
		if finalProbabilities[i] > 0.5 {
			survivors++
		}
		totalSurvivalProbability += finalProbabilities[i]
	}

	result := map[string]interface{}{
		"assignments":              assignments,
		"survivors":                survivors,
		"total_survival_probability": int(totalSurvivalProbability*100),
	}

	return result
}

func main() {
	var input map[string]interface{}
	decoder := json.NewDecoder(SystemIn)
	err := decoder.Decode(&input)
	if err != nil {
		panic(err)
	}

	patients := input["patients"].([]interface{})
	patientsData := make([][]int, len(patients))
	for i, patient := range patients {
		patientData := patient.([]interface{})
		patientsData[i] = make([]int, len(patientData))
		for j, prob := range patientData {
			patientsData[i][j] = int(prob.(float64))
		}
	}

	resources := input["resources"].([]interface{})
	resourcesData := make([]map[string]interface{}, len(resources))
	for i, resource := range resources {
		resourceData := resource.(map[string]interface{})
		resourcesData[i] = resourceData
	}

	responders := int(input["responders"].(float64))
	totalTime := int(input["total_time"].(float64))

	result := allocateResources(patientsData, resourcesData, responders, totalTime)

	jsonResult, err := json.Marshal(result)
	if err != nil {
		panic(err)
	}

	fmt.Println(string(jsonResult))
}