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

	for _, w := range wards {
		ward := w.(map[string]interface{})
		if matchWard(patient, ward) {
			// Try regular beds
			if beds, ok := ward["available_beds"].([]interface{}); ok && len(beds) > 0 {
				result["assigned_ward"] = ward["ward_name"]
				result["assigned_bed"] = beds[0]
				return result
			}

			// Try overflow beds
			if overflow, ok := ward["overflow_capacity"].(float64); ok && overflow > 0 {
				result["assigned_ward"] = ward["ward_name"]
				result["assigned_bed"] = fmt.Sprintf("Overflow-%d", 1)
				return result
			}

			// Try satellite hospitals
			if satellites, ok := ward["satellite_hospitals"].([]interface{}); ok && len(satellites) > 0 {
				result["assigned_satellite_hospital"] = satellites[0]
				return result
			}
		}
	}

	return result
}

func matchWard(patient, ward map[string]interface{}) bool {
	// Match condition
	if patient["condition"] != ward["target_condition"] {
		return false
	}

	// Match gender
	patientGender := patient["gender"].(string)
	wardGender := ward["gender_restriction"].(string)
	if wardGender == "Male Only" && patientGender != "Male" {
		return false
	}
	if wardGender == "Female Only" && patientGender != "Female" {
		return false
	}

	// Match age
	patientAge := int(patient["age"].(float64))
	ageRestriction := ward["age_restriction"].([]interface{})
	minAge := int(ageRestriction[0].(float64))
	maxAge := int(ageRestriction[1].(float64))
	if patientAge < minAge || patientAge > maxAge {
		return false
	}

	// Match special requirements
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
		Patient map[string]interface{}   `json:"patient"`
		Wards   []interface{}            `json:"wards"`
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