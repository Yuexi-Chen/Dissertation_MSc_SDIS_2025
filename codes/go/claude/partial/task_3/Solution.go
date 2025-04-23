package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
)

type Emergency struct {
	ID                 string   `json:"id"`
	RegionID           string   `json:"region_id"`
	Severity           string   `json:"severity"`
	Type               string   `json:"type"`
	SpecialRequirements []string `json:"special_requirements"`
}

type Ambulance struct {
	ID            string   `json:"id"`
	Capabilities  []string `json:"capabilities"`
	CurrentRegion string   `json:"current_region"`
	Status        string   `json:"status"`
}

type Hospital struct {
	ID               string   `json:"id"`
	RegionID         string   `json:"region_id"`
	Capabilities     []string `json:"capabilities"`
	EmergencyCapacity string   `json:"emergency_capacity"`
}

type Region struct {
	RegionID        string             `json:"region_id"`
	Type            string             `json:"type"`
	Speed           int                `json:"speed"`
	Distances       map[string]float64 `json:"distances"`
	CongestionFactor float64            `json:"congestion_factor"`
	BlockedRoutes   []string           `json:"blocked_routes"`
}

type Graph struct {
	Nodes map[string]*Node
}

type Node struct {
	ID       string
	Edges    map[string]float64
	Distance float64
	Visited  bool
}

func newGraph() *Graph {
	return &Graph{Nodes: make(map[string]*Node)}
}

func (g *Graph) addNode(id string) {
	if _, exists := g.Nodes[id]; !exists {
		g.Nodes[id] = &Node{ID: id, Edges: make(map[string]float64), Distance: math.Inf(1)}
	}
}

func (g *Graph) addEdge(from, to string, weight float64) {
	g.addNode(from)
	g.addNode(to)
	g.Nodes[from].Edges[to] = weight
	g.Nodes[to].Edges[from] = weight
}

func dijkstra(graph *Graph, start string) {
	graph.Nodes[start].Distance = 0

	for len(graph.Nodes) > 0 {
		minNode := getMinDistanceNode(graph)
		if minNode == nil {
			break
		}

		for neighbor, weight := range minNode.Edges {
			if !graph.Nodes[neighbor].Visited {
				newDist := minNode.Distance + weight
				if newDist < graph.Nodes[neighbor].Distance {
					graph.Nodes[neighbor].Distance = newDist
				}
			}
		}

		minNode.Visited = true
	}
}

func getMinDistanceNode(graph *Graph) *Node {
	var minNode *Node
	minDist := math.Inf(1)

	for _, node := range graph.Nodes {
		if !node.Visited && node.Distance < minDist {
			minNode = node
			minDist = node.Distance
		}
	}

	return minNode
}

func dispatchAmbulance(emergency_event map[string]interface{}, ambulances []interface{}, hospitals []interface{}, regions []interface{}) map[string]interface{} {
	graph := buildGraph(regions)
	emergency := parseEmergency(emergency_event)
	availableAmbulances := parseAmbulances(ambulances)
	availableHospitals := parseHospitals(hospitals)

	selectedAmbulance := selectAmbulance(emergency, availableAmbulances, graph)
	if selectedAmbulance == nil {
		return createResponse(emergency.ID, nil, nil)
	}

	selectedHospital := selectHospital(emergency, selectedAmbulance, availableHospitals, graph)
	if selectedHospital == nil {
		return createResponse(emergency.ID, selectedAmbulance.ID, nil)
	}

	return createResponse(emergency.ID, selectedAmbulance.ID, selectedHospital.ID)
}

func buildGraph(regions []interface{}) *Graph {
	graph := newGraph()

	for _, r := range regions {
		region := r.(map[string]interface{})
		regionID := region["region_id"].(string)
		distances := region["distances"].(map[string]interface{})
		congestionFactor := region["congestion_factor"].(float64)
		speed := float64(region["speed"].(float64))

		for destID, distance := range distances {
			weight := (distance.(float64) / (speed * congestionFactor)) * 60
			graph.addEdge(regionID, destID, weight)
		}
	}

	return graph
}

func parseEmergency(event map[string]interface{}) Emergency {
	return Emergency{
		ID:                 event["id"].(string),
		RegionID:           event["region_id"].(string),
		Severity:           event["severity"].(string),
		Type:               event["type"].(string),
		SpecialRequirements: parseStringSlice(event["special_requirements"].([]interface{})),
	}
}

func parseAmbulances(ambulances []interface{}) []Ambulance {
	result := make([]Ambulance, len(ambulances))
	for i, a := range ambulances {
		ambulance := a.(map[string]interface{})
		result[i] = Ambulance{
			ID:            ambulance["id"].(string),
			Capabilities:  parseStringSlice(ambulance["capabilities"].([]interface{})),
			CurrentRegion: ambulance["current_region"].(string),
			Status:        ambulance["status"].(string),
		}
	}
	return result
}

func parseHospitals(hospitals []interface{}) []Hospital {
	result := make([]Hospital, len(hospitals))
	for i, h := range hospitals {
		hospital := h.(map[string]interface{})
		result[i] = Hospital{
			ID:               hospital["id"].(string),
			RegionID:         hospital["region_id"].(string),
			Capabilities:     parseStringSlice(hospital["capabilities"].([]interface{})),
			EmergencyCapacity: hospital["emergency_capacity"].(string),
		}
	}
	return result
}

func parseStringSlice(slice []interface{}) []string {
	result := make([]string, len(slice))
	for i, v := range slice {
		result[i] = v.(string)
	}
	return result
}

func selectAmbulance(emergency Emergency, ambulances []Ambulance, graph *Graph) *Ambulance {
	var bestAmbulance *Ambulance
	bestTime := math.Inf(1)

	for i := range ambulances {
		ambulance := &ambulances[i]
		if ambulance.Status != "Available" {
			continue
		}

		if !meetsCapabilityRequirements(ambulance, emergency) {
			continue
		}

		dijkstra(graph, ambulance.CurrentRegion)
		arrivalTime := graph.Nodes[emergency.RegionID].Distance

		if arrivalTime < bestTime || (arrivalTime == bestTime && comparePriority(ambulance, bestAmbulance)) {
			bestAmbulance = ambulance
			bestTime = arrivalTime
		}
	}

	return bestAmbulance
}

func meetsCapabilityRequirements(ambulance *Ambulance, emergency Emergency) bool {
	if emergency.Severity == "Critical" {
		return contains(ambulance.Capabilities, "Advanced Life Support")
	}
	return true
}

func comparePriority(a1, a2 *Ambulance) bool {
	if len(a1.Capabilities) != len(a2.Capabilities) {
		return len(a1.Capabilities) > len(a2.Capabilities)
	}
	return a1.ID < a2.ID
}

func selectHospital(emergency Emergency, ambulance *Ambulance, hospitals []Hospital, graph *Graph) *Hospital {
	var bestHospital *Hospital
	bestTime := math.Inf(1)

	for i := range hospitals {
		hospital := &hospitals[i]
		if !meetsHospitalRequirements(hospital, emergency) {
			continue
		}

		dijkstra(graph, emergency.RegionID)
		arrivalTime := graph.Nodes[hospital.RegionID].Distance

		if arrivalTime < bestTime || (arrivalTime == bestTime && compareHospitalPriority(hospital, bestHospital)) {
			bestHospital = hospital
			bestTime = arrivalTime
		}
	}

	return bestHospital
}

func meetsHospitalRequirements(hospital *Hospital, emergency Emergency) bool {
	if emergency.Severity == "Critical" {
		return true
	}
	return contains(hospital.Capabilities, emergency.Type+" Center")
}

func compareHospitalPriority(h1, h2 *Hospital) bool {
	capacityOrder := map[string]int{"High": 3, "Medium": 2, "Low": 1}
	return capacityOrder[h1.EmergencyCapacity] > capacityOrder[h2.EmergencyCapacity]
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func createResponse(emergencyID string, ambulanceID, hospitalID interface{}) map[string]interface{} {
	return map[string]interface{}{
		"emergency_id":        emergencyID,
		"assigned_ambulance":  ambulanceID,
		"destination_hospital": hospitalID,
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