package main

import (
	"encoding/json"
	"fmt"
	"math"
)

// Region represents a region node in the graph
type Region struct {
	ID              string
	Type            string
	Speed           float64
	Distances       map[string]float64
	CongestionFactor float64
	BlockedRoutes   []string
}

// Ambulance represents an ambulance with capabilities and current status
type Ambulance struct {
	ID             string
	Capabilities   []string
	CurrentRegion  string
	Status         string
}

// Hospital represents a hospital with capabilities and capacity
type Hospital struct {
	ID                string
	RegionID          string
	Capabilities      []string
	EmergencyCapacity string
}

// Graph represents the network of regions
type Graph map[string]Region

// EmergencyEvent represents an emergency event
type EmergencyEvent struct {
	ID                 string
	RegionID           string
	Severity           string
	Type               string
	SpecialRequirements []string
}

func calculateTravelTime(distance, speed, congestionFactor float64) float64 {
	return (distance / (speed * congestionFactor)) * 60
}

func buildGraph(regions []interface{}) Graph {
	graph := make(Graph)
	for _, r := range regions {
		regionMap := r.(map[string]interface{})
		region := Region{
			ID:              regionMap["region_id"].(string),
			Type:            regionMap["type"].(string),
			Speed:           regionMap["speed"].(float64),
			CongestionFactor: regionMap["congestion_factor"].(float64),
			Distances:       make(map[string]float64),
			BlockedRoutes:   make([]string, len(regionMap["blocked_routes"].([]interface{}))),
		}
		for dest, dist := range regionMap["distances"].(map[string]interface{}) {
			region.Distances[dest] = dist.(float64)
		}
		for i, br := range regionMap["blocked_routes"].([]interface{}) {
			region.BlockedRoutes[i] = br.(string)
		}
		graph[region.ID] = region
	}
	return graph
}

func dijkstra(graph Graph, start string) map[string]float64 {
	dist := make(map[string]float64)
	for node := range graph {
		dist[node] = math.Inf(1)
	}
	dist[start] = 0

	visited := make(map[string]bool)

	for len(visited) < len(graph) {
		minDist := math.Inf(1)
		minNode := ""

		for node, distance := range dist {
			if !visited[node] && distance < minDist {
				minDist = distance
				minNode = node
			}
		}

		if minNode == "" {
			break
		}

		visited[minNode] = true
		for neighbor, distance := range graph[minNode].Distances {
			if contains(graph[minNode].BlockedRoutes, neighbor) {
				continue
			}
			alt := dist[minNode] + calculateTravelTime(distance, graph[minNode].Speed, graph[minNode].CongestionFactor)
			if alt < dist[neighbor] {
				dist[neighbor] = alt
			}
		}
	}
	return dist
}

func contains(slice []string, item string) bool {
	for _, a := range slice {
		if a == item {
			return true
		}
	}
	return false
}

func findBestAmbulance(event EmergencyEvent, ambulances []interface{}, graph Graph) *Ambulance {
	dists := dijkstra(graph, event.RegionID)
	var bestAmbulance *Ambulance
	minTime := math.Inf(1)

	for _, a := range ambulances {
		am := a.(map[string]interface{})
		if am["status"].(string) != "Available" {
			continue
		}
		amb := Ambulance{
			ID:             am["id"].(string),
			Capabilities:   make([]string, len(am["capabilities"].([]interface{}))),
			CurrentRegion:  am["current_region"].(string),
		}
		for i, c := range am["capabilities"].([]interface{}) {
			amb.Capabilities[i] = c.(string)
		}

		if event.Severity == "Critical" && !contains(amb.Capabilities, "Advanced Life Support") {
			continue
		}

		time := dists[amb.CurrentRegion]
		if time < minTime || (time == minTime && amb.ID < bestAmbulance.ID) {
			minTime = time
			bestAmbulance = &amb
		}
	}
	return bestAmbulance
}

func findBestHospital(event EmergencyEvent, ambulance *Ambulance, hospitals []interface{}, graph Graph) *Hospital {
	dists := dijkstra(graph, event.RegionID)
	var bestHospital *Hospital
	minTime := math.Inf(1)

	for _, h := range hospitals {
		hos := h.(map[string]interface{})
		hospital := Hospital{
			ID:                hos["id"].(string),
			RegionID:          hos["region_id"].(string),
			Capabilities:      make([]string, len(hos["capabilities"].([]interface{}))),
			EmergencyCapacity: hos["emergency_capacity"].(string),
		}
		for i, c := range hos["capabilities"].([]interface{}) {
			hospital.Capabilities[i] = c.(string)
		}

		if event.Severity == "Critical" && !contains(hospital.Capabilities, "Cardiac Center") && event.Type == "Cardiac" {
			continue
		}

		time := dists[hospital.RegionID]
		if time < minTime || (time == minTime && hospital.EmergencyCapacity > bestHospital.EmergencyCapacity) {
			minTime = time
			bestHospital = &hospital
		}
	}
	return bestHospital
}

func dispatchAmbulance(emergencyEvent map[string]interface{}, ambulances []interface{}, hospitals []interface{}, regions []interface{}) map[string]interface{} {
	event := EmergencyEvent{
		ID:                 emergencyEvent["id"].(string),
		RegionID:           emergencyEvent["region_id"].(string),
		Severity:           emergencyEvent["severity"].(string),
		Type:               emergencyEvent["type"].(string),
		SpecialRequirements: make([]string, len(emergencyEvent["special_requirements"].([]interface{}))),
	}
	for i, sr := range emergencyEvent["special_requirements"].([]interface{}) {
		event.SpecialRequirements[i] = sr.(string)
	}

	graph := buildGraph(regions)

	ambulance := findBestAmbulance(event, ambulances, graph)
	if ambulance == nil {
		return map[string]interface{}{
			"emergency_id":       event.ID,
			"assigned_ambulance": nil,
			"destination_hospital": nil,
		}
	}

	hospital := findBestHospital(event, ambulance, hospitals, graph)
	if hospital == nil {
		return map[string]interface{}{
			"emergency_id":       event.ID,
			"assigned_ambulance": ambulance.ID,
			"destination_hospital": nil,
		}
	}

	return map[string]interface{}{
		"emergency_id":       event.ID,
		"assigned_ambulance": ambulance.ID,
		"destination_hospital": hospital.ID,
	}
}

func main() {
	var input map[string]interface{}
	_ = json.NewDecoder(json.NewDecoder(os.Stdin)).Decode(&input)

	emergencyEvent := input["emergency_event"].(map[string]interface{})
	ambulances := input["ambulances"].([]interface{})
	hospitals := input["hospitals"].([]interface{})
	regions := input["regions"].([]interface{})

	result := dispatchAmbulance(emergencyEvent, ambulances, hospitals, regions)

	output, _ := json.Marshal(result)
	fmt.Println(string(output))
}