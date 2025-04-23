package main

import (
	"encoding/json"
	"fmt"
	"math"
	"sort"
)

// Helper functions

func calculateTravelTime(distance float64, regionType string, congestionFactor float64) float64 {
	var baseSpeed float64
	switch regionType {
	case "Urban":
		baseSpeed = 30.0
	case "Suburban":
		baseSpeed = 50.0
	case "Rural":
		baseSpeed = 80.0
	default:
		return math.Inf(1) // Indicate an error
	}

	if congestionFactor <= 0 || congestionFactor > 1 {
		return math.Inf(1) // Indicate an error
	}

	return (distance / (baseSpeed * congestionFactor)) * 60
}

func buildGraph(regions []interface{}) map[string]map[string]float64 {
	graph := make(map[string]map[string]float64)
	for _, regionInterface := range regions {
		region := regionInterface.(map[string]interface{})
		regionID := region["region_id"].(string)
		graph[regionID] = make(map[string]float64)

		distances := region["distances"].(map[string]interface{})
		for neighborID, distanceInterface := range distances {
			distance := distanceInterface.(float64)
			congestionFactor := region["congestion_factor"].(float64)
			regionType := region["type"].(string)

			travelTime := calculateTravelTime(distance, regionType, congestionFactor)

			//Check for blocked routes
			blockedRoutesInterface, ok := region["blocked_routes"]
			if ok {
				blockedRoutes := blockedRoutesInterface.([]interface{})
				for _, blockedRouteInterface := range blockedRoutes {
					blockedRoute := blockedRouteInterface.(string)
					if blockedRoute == neighborID {
						travelTime = math.Inf(1)
						break
					}
				}
			}
			graph[regionID][neighborID] = travelTime
		}
	}
	return graph
}

func dijkstra(graph map[string]map[string]float64, start string, end string) float64 {
	distances := make(map[string]float64)
	for regionID := range graph {
		distances[regionID] = math.Inf(1)
	}
	distances[start] = 0

	visited := make(map[string]bool)

	for {
		var current string
		minDistance := math.Inf(1)

		for regionID, distance := range distances {
			if !visited[regionID] && distance < minDistance {
				current = regionID
				minDistance = distance
			}
		}

		if minDistance == math.Inf(1) {
			break // No more reachable nodes
		}

		if current == end {
			break
		}

		visited[current] = true

		for neighbor, weight := range graph[current] {
			newDistance := distances[current] + weight
			if newDistance < distances[neighbor] {
				distances[neighbor] = newDistance
			}
		}
	}

	return distances[end]
}

func meetsCapabilityRequirements(ambulance map[string]interface{}, emergency map[string]interface{}) bool {
	if emergency["severity"] == "Critical" {
		specialRequirements := emergency["special_requirements"].([]interface{})
		for _, requirement := range specialRequirements {
			found := false
			for _, capability := range ambulance["capabilities"].([]interface{}) {
				if requirement == capability {
					found = true
					break
				}
			}
			if !found {
				return false
			}
		}
		return true
	}
	return true
}

func findBestHospital(emergency map[string]interface{}, ambulance map[string]interface{}, hospitals []interface{}, regions []interface{}, graph map[string]map[string]float64) (map[string]interface{}, float64) {
	var bestHospital map[string]interface{}
	minArrivalTime := math.Inf(1)

	emergencyRegion := emergency["region_id"].(string)

	for _, hospitalInterface := range hospitals {
		hospital := hospitalInterface.(map[string]interface{})
		hospitalRegion := hospital["region_id"].(string)

		arrivalTime := dijkstra(graph, emergencyRegion, hospitalRegion)
		if emergencyRegion == hospitalRegion {
			arrivalTime = 0
		}

		hospitalCapabilities := hospital["capabilities"].([]interface{})
		emergencyType := emergency["type"].(string)
		capacity := hospital["emergency_capacity"].(string)

		//Filter by matching capabilities
		capabilityMatch := false
		switch emergencyType {
		case "Cardiac":
			for _, capability := range hospitalCapabilities {
				if capability == "Cardiac Center" {
					capabilityMatch = true
					break
				}
			}
		default:
			capabilityMatch = true
		}

		if emergency["severity"] == "Critical" {
			capabilityMatch = true //prioritize response time over exact capability matching
		}

		if capabilityMatch {
			if arrivalTime < minArrivalTime {
				minArrivalTime = arrivalTime
				bestHospital = hospital
			} else if arrivalTime == minArrivalTime {
				//Prioritize by emergency capacity (High > Medium > Low)
				currentCapacityScore := 0
				bestCapacityScore := 0

				if bestHospital != nil {
					bestCapacity := bestHospital["emergency_capacity"].(string)
					if bestCapacity == "High" {
						bestCapacityScore = 3
					} else if bestCapacity == "Medium" {
						bestCapacityScore = 2
					} else if bestCapacity == "Low" {
						bestCapacityScore = 1
					}
				}

				if capacity == "High" {
					currentCapacityScore = 3
				} else if capacity == "Medium" {
					currentCapacityScore = 2
				} else if capacity == "Low" {
					currentCapacityScore = 1
				}
				if currentCapacityScore > bestCapacityScore {
					bestHospital = hospital
					minArrivalTime = arrivalTime
				}
			}
		}
	}
	return bestHospital, minArrivalTime
}

func dispatchAmbulance(emergency_event map[string]interface{}, ambulances []interface{}, hospitals []interface{}, regions []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"emergency_id":        emergency_event["id"],
		"assigned_ambulance":  nil,
		"destination_hospital": nil,
	}

	graph := buildGraph(regions)

	var bestAmbulance map[string]interface{}
	minResponseTime := math.Inf(1)

	emergencyRegion := emergency_event["region_id"].(string)

	// Step 1: Select the fastest ambulance
	for _, ambulanceInterface := range ambulances {
		ambulance := ambulanceInterface.(map[string]interface{})
		if ambulance["status"] == "Available" && meetsCapabilityRequirements(ambulance, emergency_event) {
			ambulanceRegion := ambulance["current_region"].(string)
			responseTime := dijkstra(graph, ambulanceRegion, emergencyRegion)
			if ambulanceRegion == emergencyRegion {
				responseTime = 0
			}

			if responseTime < minResponseTime {
				minResponseTime = responseTime
				bestAmbulance = ambulance
			} else if responseTime == minResponseTime {
				// For tied arrival times, prioritize by capabilities, then lower ID
				if len(ambulance["capabilities"].([]interface{})) > len(bestAmbulance["capabilities"].([]interface{})) {
					bestAmbulance = ambulance
				} else if ambulance["id"].(string) < bestAmbulance["id"].(string) {
					bestAmbulance = ambulance
				}
			}
		}
	}

	if bestAmbulance != nil {
		result["assigned_ambulance"] = bestAmbulance["id"]

		// Step 2: Choose the best hospital
		bestHospital, _ := findBestHospital(emergency_event, bestAmbulance, hospitals, regions, graph)

		if bestHospital != nil {
			result["destination_hospital"] = bestHospital["id"]
		}
	}

	return result
}

func main() {
	var input map[string]interface{}
	decoder := json.NewDecoder(SystemIn{})
	err := decoder.Decode(&input)
	if err != nil {
		fmt.Println("Error decoding JSON:", err)
		return
	}

	emergencyEvent := input["emergency_event"].(map[string]interface{})
	ambulances := input["ambulances"].([]interface{})
	hospitals := input["hospitals"].([]interface{})
	regions := input["regions"].([]interface{})

	result := dispatchAmbulance(emergencyEvent, ambulances, hospitals, regions)

	jsonResult, err := json.Marshal(result)
	if err != nil {
		fmt.Println("Error encoding JSON:", err)
		return
	}

	fmt.Println(string(jsonResult))
}

// SystemIn simulates stdin for local testing
type SystemIn struct{}

func (s SystemIn) Read(p []byte) (n int, err error) {
	inputJSON := `{
		"emergency_event": {
			"id": "E001",
			"region_id": "R1",
			"severity": "Critical",
			"type": "Cardiac",
			"special_requirements": ["Advanced Life Support", "Defibrillator"]
		},
		"ambulances": [{
			"id": "A1",
			"capabilities": ["Cardiac Support", "Trauma Care", "Defibrillator"],
			"current_region": "R1",
			"status": "Available"
		}, {
			"id": "A3",
			"capabilities": ["Cardiac Support", "Trauma Care", "Defibrillator"],
			"current_region": "R3",
			"status": "Available"
		}],
		"hospitals": [{
			"id": "H1",
			"region_id": "R2",
			"capabilities": ["Trauma Center", "Cardiac Center", "Stroke Unit"],
			"emergency_capacity": "High"
		}, {
			"id": "H2",
			"region_id": "R1",
			"capabilities": ["General Emergency", "Minor Injuries"],
			"emergency_capacity": "Medium"
		}],
		"regions": [{
			"region_id": "R1",
			"type": "Urban",
			"speed": 30,
			"distances": {
				"R2": 5,
				"R3": 7
			},
			"congestion_factor": 0.5,
			"blocked_routes": []
		}, {
			"region_id": "R2",
			"type": "Suburban",
			"speed": 50,
			"distances": {
				"R1": 5,
				"R3": 8
			},
			"congestion_factor": 1.0,
			"blocked_routes": []
		}, {
			"region_id": "R3",
			"type": "Suburban",
			"speed": 50,
			"distances": {
				"R1": 7,
				"R2": 8
			},
			"congestion_factor": 1.0,
			"blocked_routes": []
		}]
	}`
	copy(p, []byte(inputJSON))
	return len(inputJSON), nil
}