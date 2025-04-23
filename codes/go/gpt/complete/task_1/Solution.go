package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func allocateBed(patient map[string]interface{}, wards []interface{}) map[string]interface{} {
	patientID := patient["id"].(string)
	gender := patient["gender"].(string)
	age := int(patient["age"].(float64))
	condition := patient["condition"].(string)
	specialRequirements, _ := patient["special_requirements"].([]interface{})

	for _, w := range wards {
		ward := w.(map[string]interface{})
		if !matchesWard(patient, ward) {
			continue
		}

		if availableBeds, ok := ward["available_beds"].([]interface{}); ok && len(availableBeds) > 0 {
			assignedBed := int(availableBeds[0].(float64))
			return map[string]interface{}{
				"patient_id":                 patientID,
				"assigned_ward":             ward["ward_name"].(string),
				"assigned_bed":              assignedBed,
				"assigned_satellite_hospital": nil,
			}
		}

		if overflowCapacity, ok := ward["overflow_capacity"].(float64); ok && overflowCapacity > 0 {
			return map[string]interface{}{
				"patient_id":                 patientID,
				"assigned_ward":             ward["ward_name"].(string),
				"assigned_bed":              fmt.Sprintf("Overflow-%d", 1),
				"assigned_satellite_hospital": nil,
			}
		}

		if satelliteHospitals, ok := ward["satellite_hospitals"].([]interface{}); ok && len(satelliteHospitals) > 0 {
			return map[string]interface{}{
				"patient_id":                 patientID,
				"assigned_ward":             nil,
				"assigned_bed":              nil,
				"assigned_satellite_hospital": satelliteHospitals[0].(string),
			}
		}
	}

	return map[string]interface{}{
		"patient_id":                 patientID,
		"assigned_ward":             nil,
		"assigned_bed":              nil,
		"assigned_satellite_hospital": nil,
	}
}

func matchesWard(patient map[string]interface{}, ward map[string]interface{}) bool {
	gender := patient["gender"].(string)
	age := int(patient["age"].(float64))
	condition := patient["condition"].(string)
	specialRequirements, _ := patient["special_requirements"].([]interface{})

	genderRestriction := ward["gender_restriction"].(string)
	ageRestriction := ward["age_restriction"].([]interface{})
	minAge := int(ageRestriction[0].(float64))
	maxAge := int(ageRestriction[1].(float64))
	targetCondition := ward["target_condition"].(string)
	wardSpecialRequirements, _ := ward["special_requirements"].([]interface{})

	if targetCondition != condition {
		return false
	}

	if !(genderRestriction == "No Restriction" || genderRestriction == "No Gender Restriction" ||
		(genderRestriction == "Male Only" && gender == "Male") ||
		(genderRestriction == "Female Only" && gender == "Female")) {
		return false
	}

	if age < minAge || age > maxAge {
		return false
	}

	for _, req := range specialRequirements {
		found := false
		for _, wardReq := range wardSpecialRequirements {
			if req == wardReq {
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

func main() {
	var input struct {
		Patient map[string]interface{} `json:"patient"`
		Wards   []interface{}          `json:"wards"`
	}

	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil {
		fmt.Println("Error decoding input:", err)
		return
	}

	result := allocateBed(input.Patient, input.Wards)

	output, err := json.Marshal(result)
	if err != nil {
		fmt.Println("Error encoding output:", err)
		return
	}

	fmt.Println(string(output))
}