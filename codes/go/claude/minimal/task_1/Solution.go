package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func allocateBed(patient map[string]interface{}, wards []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"patient_id":                 patient["id"],
		"assigned_ward":              nil,
		"assigned_bed":               nil,
		"assigned_satellite_hospital": nil,
	}

	for _, ward := range wards {
		wardMap := ward.(map[string]interface{})
		if matchWard(patient, wardMap) {
			// Step 1: Regular beds
			if beds, ok := wardMap["available_beds"].([]interface{}); ok && len(beds) > 0 {
				result["assigned_ward"] = wardMap["ward_name"]
				result["assigned_bed"] = beds[0]
				return result
			}

			// Step 2: Overflow beds
			if overflow, ok := wardMap["overflow_capacity"].(float64); ok && overflow > 0 {
				result["assigned_ward"] = wardMap["ward_name"]
				result["assigned_bed"] = fmt.Sprintf("Overflow-%d", 1)
				return result
			}

			// Step 3: Satellite hospitals
			if satellites, ok := wardMap["satellite_hospitals"].([]interface{}); ok && len(satellites) > 0 {
				result["assigned_satellite_hospital"] = satellites[0]
				return result
			}
		}
	}

	return result
}

func matchWard(patient, ward map[string]interface{}) bool {
	if patient["condition"] != ward["target_condition"] {
		return false
	}

	if ward["gender_restriction"] == "Male Only" && patient["gender"] != "Male" {
		return false
	}

	if ward["gender_restriction"] == "Female Only" && patient["gender"] != "Female" {
		return false
	}

	age := patient["age"].(float64)
	ageRestriction := ward["age_restriction"].([]interface{})
	if age < ageRestriction[0].(float64) || age > ageRestriction[1].(float64) {
		return false
	}

	patientReqs := patient["special_requirements"].([]interface{})
	wardReqs := ward["special_requirements"].([]interface{})
	for _, req := range patientReqs {
		if !contains(wardReqs, req) {
			return false
		}
	}

	return true
}

func contains(slice []interface{}, item interface{}) bool {
	for _, v := range slice {
		if v == item {
			return true
		}
	}
	return false
}

func main() {
	var input struct {
		Patient map[string]interface{} `json:"patient"`
		Wards   []interface{}          `json:"wards"`
	}

	decoder := json.NewDecoder(os.Stdin)
	if err := decoder.Decode(&input); err != nil {
		fmt.Fprintf(os.Stderr, "Error decoding input: %v\n", err)
		os.Exit(1)
	}

	result := allocateBed(input.Patient, input.Wards)

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(result); err != nil {
		fmt.Fprintf(os.Stderr, "Error encoding output: %v\n", err)
		os.Exit(1)
	}
}