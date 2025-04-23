package main

import (
	"encoding/json"
	"fmt"
	"math"
	"sort"
)

func dispatchAmbulance(emergency_event map[string]interface{}, ambulances []interface{}, hospitals []interface{}, regions []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"emergency_id":         emergency_event["id"],
		"assigned_ambulance":   nil,
		"destination_hospital": nil,
	}

	emergencyRegionID := emergency_event["region_id"].(string)
	severity := emergency_event["severity"].(string)
	eventType := emergency_event["type"].(string)
	specialRequirements := emergency_event["special_requirements"].([]interface{})

	// --- Step 1: Select the fastest ambulance ---
	var bestAmbulance map[string]interface{}
	minAmbulanceTime := math.MaxFloat64

	for _, ambulanceInterface := range ambulances {
		ambulance := ambulanceInterface.(map[string]interface{})
		if ambulance["status"] == "Available" {
			ambulanceCapabilities := ambulance["capabilities"].([]interface{})
			currentRegion := ambulance["current_region"].(string)

			// Check if ambulance meets capability requirements
			meetsRequirements := true
			if severity == "Critical" && contains(specialRequirements, "Advanced Life Support") {
				hasALS := false
				for _, cap := range ambulanceCapabilities {
					if cap == "Advanced Life Support" {
						hasALS = true
						break
					}
				}
				if !hasALS {
					meetsRequirements = false
				}
			}

			if meetsRequirements {
				// Calculate response time
				responseTime := calculateShortestPath(currentRegion, emergencyRegionID, regions)

				if responseTime < minAmbulanceTime {
					minAmbulanceTime = responseTime
					bestAmbulance = ambulance
				} else if responseTime == minAmbulanceTime {
					// Prioritize by capabilities, then lower ID
					if len(ambulanceCapabilities) > len(bestAmbulance["capabilities"].([]interface{})) {
						bestAmbulance = ambulance
					} else if ambulance["id"].(string) < bestAmbulance["id"].(string) {
						bestAmbulance = ambulance
					}
				}
			}
		}
	}

	if bestAmbulance == nil {
		return result
	}

	result["assigned_ambulance"] = bestAmbulance["id"]

	// --- Step 2: Choose the best hospital ---
	var bestHospital map[string]interface{}
	minHospitalTime := math.MaxFloat64

	for _, hospitalInterface := range hospitals {
		hospital := hospitalInterface.(map[string]interface{})
		hospitalRegionID := hospital["region_id"].(string)
		hospitalCapabilities := hospital["capabilities"].([]interface{})
		emergencyCapacity := hospital["emergency_capacity"].(string)

		// Filter by matching capabilities
		meetsCapability := true
		if eventType == "Cardiac" {
			hasCardiacCenter := false
			for _, cap := range hospitalCapabilities {
				if cap == "Cardiac Center" {
					hasCardiacCenter = true
					break
				}
			}
			if !hasCardiacCenter && severity != "Critical" {
				meetsCapability = false
			}
		}

		if meetsCapability {
			// Calculate hospital arrival time
			hospitalArrivalTime := calculateShortestPath(emergencyRegionID, hospitalRegionID, regions)

			if hospitalArrivalTime < minHospitalTime {
				minHospitalTime = hospitalArrivalTime
				bestHospital = hospital
			} else if hospitalArrivalTime == minHospitalTime {
				// Prioritize by emergency capacity (High > Medium > Low)
				if emergencyCapacity == "High" && bestHospital["emergency_capacity"] != "High" {
					bestHospital = hospital
				} else if emergencyCapacity == "Medium" && bestHospital["emergency_capacity"] != "High" && bestHospital["emergency_capacity"] != "Medium" {
					bestHospital = hospital
				}
			}
		}
	}

	//If no suitable hospital: select nearest with emergency services
	if bestHospital == nil {
		minHospitalTime = math.MaxFloat64
		for _, hospitalInterface := range hospitals {
			hospital := hospitalInterface.(map[string]interface{})
			hospitalRegionID := hospital["region_id"].(string)
			hospitalArrivalTime := calculateShortestPath(emergencyRegionID, hospitalRegionID, regions)

			if hospitalArrivalTime < minHospitalTime {
				minHospitalTime = hospitalArrivalTime
				bestHospital = hospital
			}
		}
	}

	if bestHospital != nil {
		result["destination_hospital"] = bestHospital["id"]
	}

	return result
}

func calculateShortestPath(startRegionID string, endRegionID string, regions []interface{}) float64 {
	if startRegionID == endRegionID {
		return 0.0
	}

	graph := make(map[string]map[string]float64)
	regionMap := make(map[string]map[string]interface{})

	for _, regionInterface := range regions {
		region := regionInterface.(map[string]interface{})
		regionID := region["region_id"].(string)
		regionMap[regionID] = region

		graph[regionID] = make(map[string]float64)
		distances := region["distances"].(map[string]interface{})
		speed := region["speed"].(float64)
		congestionFactor := region["congestion_factor"].(float64)
		blockedRoutes := region["blocked_routes"].([]interface{})

		for neighborID, distanceInterface := range distances {
			distance := distanceInterface.(float64)

			isBlocked := false
			for _, blockedRouteInterface := range blockedRoutes {
				blockedRoute := blockedRouteInterface.(string)
				if blockedRoute == neighborID {
					isBlocked = true
					break
				}
			}

			if isBlocked {
				graph[regionID][neighborID] = math.MaxFloat64
			} else {
				baseSpeed := 0.0
				regionType := region["type"].(string)
				if regionType == "Urban" {
					baseSpeed = 30.0
				} else if regionType == "Suburban" {
					baseSpeed = 50.0
				} else {
					baseSpeed = 80.0
				}

				travelTime := distance / (baseSpeed * congestionFactor) * 60.0
				graph[regionID][neighborID] = travelTime
			}
		}
	}

	distances := make(map[string]float64)
	for regionID := range graph {
		distances[regionID] = math.MaxFloat64
	}
	distances[startRegionID] = 0.0

	visited := make(map[string]bool)

	for i := 0; i < len(graph); i++ {
		closestRegion := ""
		minDistance := math.MaxFloat64

		for regionID, distance := range distances {
			if !visited[regionID] && distance < minDistance {
				minDistance = distance
				closestRegion = regionID
			}
		}

		if closestRegion == "" {
			break
		}

		visited[closestRegion] = true

		for neighborID, weight := range graph[closestRegion] {
			if distances[closestRegion]+weight < distances[neighborID] {
				distances[neighborID] = distances[closestRegion] + weight
			}
		}
	}

	return math.Round(distances[endRegionID])
}

func contains(slice []interface{}, item interface{}) bool {
	for _, element := range slice {
		if element == item {
			return true
		}
	}
	return false
}

func main() {
	var input map[string]interface{}
	if err := json.NewDecoder(System.Stdin).Decode(&input); err != nil {
		panic(err)
	}

	emergency_event := input["emergency_event"].(map[string]interface{})
	ambulances := input["ambulances"].([]interface{})
	hospitals := input["hospitals"].([]interface{})
	regions := input["regions"].([]interface{})

	result := dispatchAmbulance(emergency_event, ambulances, hospitals, regions)

	jsonResult, err := json.Marshal(result)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(jsonResult))
}