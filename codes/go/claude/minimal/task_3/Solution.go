package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
)

func dispatchAmbulance(emergency_event map[string]interface{}, ambulances []interface{}, hospitals []interface{}, regions []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"emergency_id":        emergency_event["id"],
		"assigned_ambulance":  nil,
		"destination_hospital": nil,
	}

	graph := constructGraph(regions)
	emergencyRegion := emergency_event["region_id"].(string)
	severity := emergency_event["severity"].(string)
	emergencyType := emergency_event["type"].(string)

	// Step 1: Select the fastest ambulance
	var bestAmbulance map[string]interface{}
	bestTime := math.Inf(1)

	for _, amb := range ambulances {
		ambulance := amb.(map[string]interface{})
		if ambulance["status"].(string) != "Available" {
			continue
		}

		if severity == "Critical" && !contains(ambulance["capabilities"].([]interface{}), "Advanced Life Support") {
			continue
		}

		ambRegion := ambulance["current_region"].(string)
		time := dijkstra(graph, ambRegion, emergencyRegion)

		if time < bestTime || (time == bestTime && ambulance["id"].(string) < bestAmbulance["id"].(string)) {
			bestTime = time
			bestAmbulance = ambulance
		}
	}

	if bestAmbulance == nil {
		return result
	}

	result["assigned_ambulance"] = bestAmbulance["id"]

	// Step 2: Choose the best hospital
	var bestHospital map[string]interface{}
	bestTime = math.Inf(1)

	for _, hosp := range hospitals {
		hospital := hosp.(map[string]interface{})
		if !contains(hospital["capabilities"].([]interface{}), emergencyType+"Center") && severity != "Critical" {
			continue
		}

		hospRegion := hospital["region_id"].(string)
		time := dijkstra(graph, emergencyRegion, hospRegion)

		if time < bestTime || (time == bestTime && getCapacityScore(hospital["emergency_capacity"].(string)) > getCapacityScore(bestHospital["emergency_capacity"].(string))) {
			bestTime = time
			bestHospital = hospital
		}
	}

	if bestHospital != nil {
		result["destination_hospital"] = bestHospital["id"]
	}

	return result
}

func constructGraph(regions []interface{}) map[string]map[string]float64 {
	graph := make(map[string]map[string]float64)

	for _, reg := range regions {
		region := reg.(map[string]interface{})
		regionID := region["region_id"].(string)
		graph[regionID] = make(map[string]float64)

		baseSpeed := getBaseSpeed(region["type"].(string))
		congestionFactor := region["congestion_factor"].(float64)
		distances := region["distances"].(map[string]interface{})

		for destRegion, distance := range distances {
			travelTime := (distance.(float64) / (baseSpeed * congestionFactor)) * 60
			graph[regionID][destRegion] = travelTime
		}

		for _, blockedRoute := range region["blocked_routes"].([]interface{}) {
			graph[regionID][blockedRoute.(string)] = math.Inf(1)
		}
	}

	return graph
}

func dijkstra(graph map[string]map[string]float64, start, end string) float64 {
	distances := make(map[string]float64)
	for node := range graph {
		distances[node] = math.Inf(1)
	}
	distances[start] = 0

	visited := make(map[string]bool)

	for len(visited) < len(graph) {
		current := minDistance(distances, visited)
		if current == end {
			return distances[end]
		}

		visited[current] = true

		for neighbor, weight := range graph[current] {
			if !visited[neighbor] {
				newDist := distances[current] + weight
				if newDist < distances[neighbor] {
					distances[neighbor] = newDist
				}
			}
		}
	}

	return distances[end]
}

func minDistance(distances map[string]float64, visited map[string]bool) string {
	min := math.Inf(1)
	var minNode string

	for node, dist := range distances {
		if !visited[node] && dist < min {
			min = dist
			minNode = node
		}
	}

	return minNode
}

func getBaseSpeed(regionType string) float64 {
	switch regionType {
	case "Urban":
		return 30
	case "Suburban":
		return 50
	case "Rural":
		return 80
	default:
		return 50
	}
}

func getCapacityScore(capacity string) int {
	switch capacity {
	case "High":
		return 3
	case "Medium":
		return 2
	case "Low":
		return 1
	default:
		return 0
	}
}

func contains(slice []interface{}, item string) bool {
	for _, v := range slice {
		if v.(string) == item {
			return true
		}
	}
	return false
}

func main() {
	var input struct {
		EmergencyEvent map[string]interface{}   `json:"emergency_event"`
		Ambulances     []interface{}            `json:"ambulances"`
		Hospitals      []interface{}            `json:"hospitals"`
		Regions        []interface{}            `json:"regions"`
	}

	decoder := json.NewDecoder(os.Stdin)
	if err := decoder.Decode(&input); err != nil {
		fmt.Fprintf(os.Stderr, "Error decoding input: %v\n", err)
		os.Exit(1)
	}

	result := dispatchAmbulance(input.EmergencyEvent, input.Ambulances, input.Hospitals, input.Regions)

	encoder := json.NewEncoder(os.Stdout)
	if err := encoder.Encode(result); err != nil {
		fmt.Fprintf(os.Stderr, "Error encoding output: %v\n", err)
		os.Exit(1)
	}
}