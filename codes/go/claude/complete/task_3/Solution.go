package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
)

type Region struct {
	RegionID         string             `json:"region_id"`
	Type             string             `json:"type"`
	Speed            int                `json:"speed"`
	Distances        map[string]float64 `json:"distances"`
	CongestionFactor float64            `json:"congestion_factor"`
	BlockedRoutes    []string           `json:"blocked_routes"`
}

type Ambulance struct {
	ID           string   `json:"id"`
	Capabilities []string `json:"capabilities"`
	CurrentRegion string  `json:"current_region"`
	Status       string   `json:"status"`
}

type Hospital struct {
	ID               string   `json:"id"`
	RegionID         string   `json:"region_id"`
	Capabilities     []string `json:"capabilities"`
	EmergencyCapacity string  `json:"emergency_capacity"`
}

type EmergencyEvent struct {
	ID                 string   `json:"id"`
	RegionID           string   `json:"region_id"`
	Severity           string   `json:"severity"`
	Type               string   `json:"type"`
	SpecialRequirements []string `json:"special_requirements"`
}

func dispatchAmbulance(emergency_event map[string]interface{}, ambulances []interface{}, hospitals []interface{}, regions []interface{}) map[string]interface{} {
	event := parseEmergencyEvent(emergency_event)
	parsedAmbulances := parseAmbulances(ambulances)
	parsedHospitals := parseHospitals(hospitals)
	parsedRegions := parseRegions(regions)

	graph := buildGraph(parsedRegions)
	
	selectedAmbulance := selectAmbulance(event, parsedAmbulances, graph)
	if selectedAmbulance == nil {
		return createNullResponse(event.ID)
	}

	selectedHospital := selectHospital(event, selectedAmbulance, parsedHospitals, graph)
	if selectedHospital == nil {
		return createNullResponse(event.ID)
	}

	return map[string]interface{}{
		"emergency_id":        event.ID,
		"assigned_ambulance":  selectedAmbulance.ID,
		"destination_hospital": selectedHospital.ID,
	}
}

func parseEmergencyEvent(data map[string]interface{}) EmergencyEvent {
	return EmergencyEvent{
		ID:                 data["id"].(string),
		RegionID:           data["region_id"].(string),
		Severity:           data["severity"].(string),
		Type:               data["type"].(string),
		SpecialRequirements: parseStringSlice(data["special_requirements"].([]interface{})),
	}
}

func parseAmbulances(data []interface{}) []Ambulance {
	ambulances := make([]Ambulance, len(data))
	for i, item := range data {
		amb := item.(map[string]interface{})
		ambulances[i] = Ambulance{
			ID:           amb["id"].(string),
			Capabilities: parseStringSlice(amb["capabilities"].([]interface{})),
			CurrentRegion: amb["current_region"].(string),
			Status:       amb["status"].(string),
		}
	}
	return ambulances
}

func parseHospitals(data []interface{}) []Hospital {
	hospitals := make([]Hospital, len(data))
	for i, item := range data {
		hosp := item.(map[string]interface{})
		hospitals[i] = Hospital{
			ID:               hosp["id"].(string),
			RegionID:         hosp["region_id"].(string),
			Capabilities:     parseStringSlice(hosp["capabilities"].([]interface{})),
			EmergencyCapacity: hosp["emergency_capacity"].(string),
		}
	}
	return hospitals
}

func parseRegions(data []interface{}) []Region {
	regions := make([]Region, len(data))
	for i, item := range data {
		reg := item.(map[string]interface{})
		regions[i] = Region{
			RegionID:         reg["region_id"].(string),
			Type:             reg["type"].(string),
			Speed:            int(reg["speed"].(float64)),
			Distances:        parseDistances(reg["distances"].(map[string]interface{})),
			CongestionFactor: reg["congestion_factor"].(float64),
			BlockedRoutes:    parseStringSlice(reg["blocked_routes"].([]interface{})),
		}
	}
	return regions
}

func parseStringSlice(data []interface{}) []string {
	result := make([]string, len(data))
	for i, item := range data {
		result[i] = item.(string)
	}
	return result
}

func parseDistances(data map[string]interface{}) map[string]float64 {
	result := make(map[string]float64)
	for k, v := range data {
		result[k] = v.(float64)
	}
	return result
}

func buildGraph(regions []Region) map[string]map[string]float64 {
	graph := make(map[string]map[string]float64)
	for _, region := range regions {
		graph[region.RegionID] = make(map[string]float64)
		for destRegion, distance := range region.Distances {
			if !contains(region.BlockedRoutes, destRegion) {
				travelTime := calculateTravelTime(distance, region.Speed, region.CongestionFactor)
				graph[region.RegionID][destRegion] = travelTime
			}
		}
	}
	return graph
}

func calculateTravelTime(distance, speed float64, congestionFactor float64) float64 {
	return math.Round((distance / (float64(speed) * congestionFactor)) * 60)
}

func selectAmbulance(event EmergencyEvent, ambulances []Ambulance, graph map[string]map[string]float64) *Ambulance {
	var bestAmbulance *Ambulance
	var bestTime float64 = math.Inf(1)

	for i := range ambulances {
		amb := &ambulances[i]
		if amb.Status != "Available" || !hasRequiredCapabilities(amb, event) {
			continue
		}

		time := dijkstra(graph, amb.CurrentRegion, event.RegionID)
		if time < bestTime || (time == bestTime && isBetterAmbulance(amb, bestAmbulance, event)) {
			bestTime = time
			bestAmbulance = amb
		}
	}

	return bestAmbulance
}

func selectHospital(event EmergencyEvent, ambulance *Ambulance, hospitals []Hospital, graph map[string]map[string]float64) *Hospital {
	var bestHospital *Hospital
	var bestTime float64 = math.Inf(1)

	for i := range hospitals {
		hosp := &hospitals[i]
		if !hasRequiredCapabilities(hosp, event) {
			continue
		}

		time := dijkstra(graph, event.RegionID, hosp.RegionID)
		if time < bestTime || (time == bestTime && isBetterHospital(hosp, bestHospital, event)) {
			bestTime = time
			bestHospital = hosp
		}
	}

	return bestHospital
}

func hasRequiredCapabilities(unit interface{}, event EmergencyEvent) bool {
	var capabilities []string
	switch u := unit.(type) {
	case *Ambulance:
		capabilities = u.Capabilities
	case *Hospital:
		capabilities = u.Capabilities
	}

	for _, req := range event.SpecialRequirements {
		if !contains(capabilities, req) {
			return false
		}
	}
	return true
}

func isBetterAmbulance(a, b *Ambulance, event EmergencyEvent) bool {
	if b == nil {
		return true
	}
	if event.Severity == "Critical" {
		return contains(a.Capabilities, "Advanced Life Support") && !contains(b.Capabilities, "Advanced Life Support")
	}
	return a.ID < b.ID
}

func isBetterHospital(a, b *Hospital, event EmergencyEvent) bool {
	if b == nil {
		return true
	}
	if a.EmergencyCapacity != b.EmergencyCapacity {
		return emergencyCapacityRank(a.EmergencyCapacity) > emergencyCapacityRank(b.EmergencyCapacity)
	}
	return a.ID < b.ID
}

func emergencyCapacityRank(capacity string) int {
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

func dijkstra(graph map[string]map[string]float64, start, end string) float64 {
	dist := make(map[string]float64)
	visited := make(map[string]bool)

	for node := range graph {
		dist[node] = math.Inf(1)
	}
	dist[start] = 0

	for len(visited) < len(graph) {
		u := minDistance(dist, visited)
		if u == "" {
			break
		}
		visited[u] = true

		if u == end {
			return dist[u]
		}

		for v, w := range graph[u] {
			if !visited[v] {
				alt := dist[u] + w
				if alt < dist[v] {
					dist[v] = alt
				}
			}
		}
	}

	return dist[end]
}

func minDistance(dist map[string]float64, visited map[string]bool) string {
	min := math.Inf(1)
	var minNode string
	for node, d := range dist {
		if d < min && !visited[node] {
			min = d
			minNode = node
		}
	}
	return minNode
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func createNullResponse(emergencyID string) map[string]interface{} {
	return map[string]interface{}{
		"emergency_id":        emergencyID,
		"assigned_ambulance":  nil,
		"destination_hospital": nil,
	}
}

func main() {
	var input map[string]interface{}
	err := json.NewDecoder(os.Stdin).Decode(&input)
	if err != nil {
		fmt.Println("Error reading input:", err)
		return
	}

	result := dispatchAmbulance(
		input["emergency_event"].(map[string]interface{}),
		input["ambulances"].([]interface{}),
		input["hospitals"].([]interface{}),
		input["regions"].([]interface{}),
	)

	json.NewEncoder(os.Stdout).Encode(result)
}