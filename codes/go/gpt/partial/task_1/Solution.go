package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func allocateBed(patient map[string]interface{}, wards []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"patient_id":                 patient["id"],
		"assigned_ward":             nil,
		"assigned_bed":              nil,
		"assigned_satellite_hospital": nil,
	}

	for _, w := range wards {
		ward := w.(map[string]interface{})
		if matchesWard(patient, ward) {
			if len(ward["available_beds"].([]interface{})) > 0 {
				// Assign regular bed
				result["assigned_ward"] = ward["ward_name"]
				result["assigned_bed"] = ward["available_beds"].([]interface{})[0]
				return result
			} else if ward["overflow_capacity"].(int) > 0 {
				// Assign overflow bed
				result["assigned_ward"] = ward["ward_name"]
				result["assigned_bed"] = fmt.Sprintf("Overflow-%d", 1)
				return result
			} else if len(ward["satellite_hospitals"].([]interface{})) > 0 {
				// Assign satellite hospital
				result["assigned_satellite_hospital"] = ward["satellite_hospitals"].([]interface{})[0]
				return result
			}
		}
	}
	return result
}

func matchesWard(patient map[string]interface{}, ward map[string]interface{}) bool {
	// Check condition match
	if patient["condition"] != ward["target_condition"] {
		return false
	}
	// Check gender match
	if ward["gender_restriction"] != "No Restriction" && ward["gender_restriction"] != "No Gender Restriction" {
		if patient["gender"] == "Male" && ward["gender_restriction"] != "Male Only" {
			return false
		}
		if patient["gender"] == "Female" && ward["gender_restriction"] != "Female Only" {
			return false
		}
	}
	// Check age restriction
	age := patient["age"].(int)
	ageRestriction := ward["age_restriction"].([]interface{})
	if age < ageRestriction[0].(int) || age > ageRestriction[1].(int) {
		return false
	}
	// Check special requirements
	patientRequirements := patient["special_requirements"].([]interface{})
	wardRequirements := ward["special_requirements"].([]interface{})
	for _, req := range patientRequirements {
		found := false
		for _, wReq := range wardRequirements {
			if req == wReq {
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

	json.NewDecoder(os.Stdin).Decode(&input)
	result := allocateBed(input.Patient, input.Wards)

	output, _ := json.Marshal(result)
	fmt.Println(string(output))
}