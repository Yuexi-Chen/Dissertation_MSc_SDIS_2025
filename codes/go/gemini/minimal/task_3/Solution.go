package main

import (
	"encoding/json"
	"fmt"
	"math"
	"sort"
)

type Region struct {
	RegionID        string             `json:"region_id"`
	Type            string             `json:"type"`
	Speed           int                `json:"speed"`
	Distances       map[string]float64 `json:"distances"`
	CongestionFactor float64            `json:"congestion_factor"`
	BlockedRoutes   []string           `json:"blocked_routes"`
}

type Ambulance struct {
	ID             string   `json:"id"`
	Capabilities   []string `json:"capabilities"`
	CurrentRegion  string   `json:"current_region"`
	Status         string   `json:"status"`
}

type Hospital struct {
	ID              string   `json:"id"`
	RegionID        string   `json:"region_id"`
	Capabilities    []string `json:"capabilities"`
	EmergencyCapacity string   `json:"emergency_capacity"`
}

type EmergencyEvent struct {
	ID                 string   `json:"id"`
	RegionID           string   `json:"region_id"`
	Severity           string   `json:"severity"`
	Type               string   `json:"type"`
	SpecialRequirements []string `json:"special_requirements"`
}

func dispatchAmbulance(emergency_event map[string]interface{}, ambulances []interface{}, hospitals []interface{}, regions []interface{}) map[string]interface{} {
	event := EmergencyEvent{
		ID:                 emergency_event["id"].(string),
		RegionID:           emergency_event["region_id"].(string),
		Severity:           emergency_event["severity"].(string),
		Type:               emergency_event["type"].(string),
		SpecialRequirements: emergency_event["special_requirements"].([]string),
	}

	var availableAmbulances []Ambulance
	for _, amb := range ambulances {
		ambMap := amb.(map[string]interface{})
		capabilities, ok := ambMap["capabilities"].([]interface{})
		if !ok {
			continue // Skip if capabilities is not a slice
		}

		var caps []string
		for _, cap := range capabilities {
			caps = append(caps, cap.(string))
		}

		availableAmbulances = append(availableAmbulances, Ambulance{
			ID:             ambMap["id"].(string),
			Capabilities:   caps,
			CurrentRegion:  ambMap["current_region"].(string),
			Status:         ambMap["status"].(string),
		})
	}

	var availableHospitals []Hospital
	for _, hosp := range hospitals {
		hospMap := hosp.(map[string]interface{})
		capabilities, ok := hospMap["capabilities"].([]interface{})
		if !ok {
			continue // Skip if capabilities is not a slice
		}

		var caps []string
		for _, cap := range capabilities {
			caps = append(caps, cap.(string))
		}

		availableHospitals = append(availableHospitals, Hospital{
			ID:              hospMap["id"].(string),
			RegionID:        hospMap["region_id"].(string),
			Capabilities:    caps,
			EmergencyCapacity: hospMap["emergency_capacity"].(string),
		})
	}

	var regionMap = make(map[string]Region)
	for _, reg := range regions {
		regMap := reg.(map[string]interface{})
		distancesMap, ok := regMap["distances"].(map[string]interface{})
		if !ok {
			continue // Skip if distances is not a map
		}

		distances := make(map[string]float64)
		for k, v := range distancesMap {
			distances[k] = v.(float64)
		}

		blockedRoutes, ok := regMap["blocked_routes"].([]interface{})
		if !ok {
			continue // Skip if blocked_routes is not a slice
		}

		var blocked []string
		for _, bl := range blockedRoutes {
			blocked = append(blocked, bl.(string))
		}

		regionMap[regMap["region_id"].(string)] = Region{
			RegionID:        regMap["region_id"].(string),
			Type:            regMap["type"].(string),
			Speed:           int(regMap["speed"].(float64)),
			Distances:       distances,
			CongestionFactor: regMap["congestion_factor"].(float64),
			BlockedRoutes:   blocked,
		}
	}

	// Step 1: Select the fastest ambulance
	var selectedAmbulance *Ambulance
	minTravelTime := math.Inf(1)

	for i := range availableAmbulances {
		ambulance := &availableAmbulances[i]
		if ambulance.Status != "Available" {
			continue
		}

		meetsRequirements := true
		if event.Severity == "Critical" {
			requiredCapabilities := []string{"Advanced Life Support"}
			for _, req := range requiredCapabilities {
				found := false
				for _, cap := range ambulance.Capabilities {
					if cap == req {
						found = true
						break
					}
				}
				if !found {
					meetsRequirements = false
					break
				}
			}
		}
		if !meetsRequirements {
			continue
		}

		travelTime := calculateTravelTime(ambulance.CurrentRegion, event.RegionID, regionMap)
		if travelTime < minTravelTime {
			minTravelTime = travelTime
			selectedAmbulance = ambulance
		} else if travelTime == minTravelTime {
			// Prioritize by capabilities, then lower ID
			if len(ambulance.Capabilities) > len(selectedAmbulance.Capabilities) {
				selectedAmbulance = ambulance
			} else if len(ambulance.Capabilities) == len(selectedAmbulance.Capabilities) && ambulance.ID < selectedAmbulance.ID {
				selectedAmbulance = ambulance
			}
		}
	}

	if selectedAmbulance == nil {
		return map[string]interface{}{
			"emergency_id":        event.ID,
			"assigned_ambulance":  nil,
			"destination_hospital": nil,
		}
	}

	// Step 2: Choose the best hospital
	var selectedHospital *Hospital
	minHospitalTravelTime := math.Inf(1)

	for i := range availableHospitals {
		hospital := &availableHospitals[i]

		hospitalCapabilitiesMatch := false
		if event.Type == "Cardiac" {
			for _, cap := range hospital.Capabilities {
				if cap == "Cardiac Center" {
					hospitalCapabilitiesMatch = true
					break
				}
			}
		} else {
			hospitalCapabilitiesMatch = true // Assume general compatibility for other types
		}

		if !hospitalCapabilitiesMatch && event.Severity != "Critical" {
			continue
		}

		hospitalTravelTime := calculateTravelTime(event.RegionID, hospital.RegionID, regionMap)

		priority := 0
		if hospital.EmergencyCapacity == "High" {
			priority = 3
		} else if hospital.EmergencyCapacity == "Medium" {
			priority = 2
		} else if hospital.EmergencyCapacity == "Low" {
			priority = 1
		}

		if hospitalTravelTime < minHospitalTravelTime {
			minHospitalTravelTime = hospitalTravelTime
			selectedHospital = hospital
		} else if hospitalTravelTime == minHospitalTravelTime {
			currentPriority := 0
			if selectedHospital.EmergencyCapacity == "High" {
				currentPriority = 3
			} else if selectedHospital.EmergencyCapacity == "Medium" {
				currentPriority = 2
			} else if selectedHospital.EmergencyCapacity == "Low" {
				currentPriority = 1
			}

			if priority > currentPriority {
				selectedHospital = hospital
			}
		}
	}

	if selectedHospital == nil {
		return map[string]interface{}{
			"emergency_id":        event.ID,
			"assigned_ambulance":  selectedAmbulance.ID,
			"destination_hospital": nil,
		}
	}

	return map[string]interface{}{
		"emergency_id":        event.ID,
		"assigned_ambulance":  selectedAmbulance.ID,
		"destination_hospital": selectedHospital.ID,
	}
}

func calculateTravelTime(startRegionID, endRegionID string, regionMap map[string]Region) float64 {
	if startRegionID == endRegionID {
		return 0
	}

	startRegion, startRegionExists := regionMap[startRegionID]
	endRegion, endRegionExists := regionMap[endRegionID]

	if !startRegionExists || !endRegionExists {
		return math.Inf(1)
	}

	distance, distanceExists := startRegion.Distances[endRegionID]
	blocked := false
	for _, blockedRoute := range startRegion.BlockedRoutes {
		if blockedRoute == endRegionID {
			blocked = true
			break
		}
	}

	if !distanceExists || blocked {
		return math.Inf(1)
	}

	baseSpeed := 0
	switch startRegion.Type {
	case "Urban":
		baseSpeed = 30
	case "Suburban":
		baseSpeed = 50
	case "Rural":
		baseSpeed = 80
	}

	if baseSpeed == 0 {
		return math.Inf(1)
	}
	travelTime := (distance / (float64(baseSpeed) * startRegion.CongestionFactor)) * 60
	return travelTime
}

func main() {
	var input map[string]interface{}
	decoder := json.NewDecoder(NewStdin())
	err := decoder.Decode(&input)
	if err != nil {
		fmt.Println("Error decoding JSON:", err)
		return
	}

	emergencyEvent, ok := input["emergency_event"].(map[string]interface{})
	if !ok {
		fmt.Println("Error: emergency_event is not a map")
		return
	}

	ambulances, ok := input["ambulances"].([]interface{})
	if !ok {
		fmt.Println("Error: ambulances is not a list")
		return
	}

	hospitals, ok := input["hospitals"].([]interface{})
	if !ok {
		fmt.Println("Error: hospitals is not a list")
		return
	}

	regions, ok := input["regions"].([]interface{})
	if !ok {
		fmt.Println("Error: regions is not a list")
		return
	}

	result := dispatchAmbulance(emergencyEvent, ambulances, hospitals, regions)

	jsonResult, err := json.Marshal(result)
	if err != nil {
		fmt.Println("Error marshaling JSON:", err)
		return
	}

	fmt.Println(string(jsonResult))
}

// Mock stdin for testing purposes
type MockStdin struct {
	data string
	pos  int
}

func NewStdin() *MockStdin {
	exampleInput := `{
		"emergency_event": {
			"id": "E001",
			"region_id": "R1",
			"severity": "Critical",
			"type": "Cardiac",
			"special_requirements": ["Advanced Life Support", "Defibrillator"]
		},
		"ambulances": [
			{
				"id": "A1",
				"capabilities": ["Cardiac Support", "Trauma Care", "Defibrillator", "Advanced Life Support"],
				"current_region": "R1",
				"status": "Available"
			},
			{
				"id": "A3",
				"capabilities": ["Cardiac Support", "Trauma Care", "Defibrillator"],
				"current_region": "R3",
				"status": "Available"
			}
		],
		"hospitals": [
			{
				"id": "H1",
				"region_id": "R2",
				"capabilities": ["Trauma Center", "Cardiac Center", "Stroke Unit"],
				"emergency_capacity": "High"
			},
			{
				"id": "H2",
				"region_id": "R1",
				"capabilities": ["General Emergency", "Minor Injuries"],
				"emergency_capacity": "Medium"
			}
		],
		"regions": [
			{
				"region_id": "R1",
				"type": "Urban",
				"speed": 30,
				"distances": {"R2": 5, "R3": 7},
				"congestion_factor": 0.5,
				"blocked_routes": []
			},
			{
				"region_id": "R2",
				"type": "Suburban",
				"speed": 50,
				"distances": {"R1": 5, "R3": 8},
				"congestion_factor": 1.0,
				"blocked_routes": []
			},
			{
				"region_id": "R3",
				"type": "Suburban",
				"speed": 50,
				"distances": {"R1": 7, "R2": 8},
				"congestion_factor": 1.0,
				"blocked_routes": []
			}
		]
	}`
	return &MockStdin{data: exampleInput, pos: 0}
}

func (s *MockStdin) Read(p []byte) (n int, err error) {
	if s.pos >= len(s.data) {
		return 0, fmt.Errorf("EOF")
	}
	n = copy(p, s.data[s.pos:])
	s.pos += n
	return n, nil
}
