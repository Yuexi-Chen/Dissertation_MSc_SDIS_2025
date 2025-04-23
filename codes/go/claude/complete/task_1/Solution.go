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
			// Try regular beds
			availableBeds := wardMap["available_beds"].([]interface{})
			if len(availableBeds) > 0 {
				result["assigned_ward"] = wardMap["ward_name"]
				result["assigned_bed"] = availableBeds[0]
				return result
			}

			// Try overflow beds
			overflowCapacity := int(wardMap["overflow_capacity"].(float64))
			if overflowCapacity > 0 {
				result["assigned_ward"] = wardMap["ward_name"]
				result["assigned_bed"] = fmt.Sprintf("Overflow-%d", 1)
				return result
			}

			// Try satellite hospitals
			satelliteHospitals := wardMap["satellite_hospitals"].([]interface{})
			if len(satelliteHospitals) > 0 {
				result["assigned_satellite_hospital"] = satelliteHospitals[0]
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
	patientReqs, patientReqsExist := patient["special_requirements"].([]interface{})
	wardReqs, wardReqsExist := ward["special_requirements"].([]interface{})

	if patientReqsExist && len(patientReqs) > 0 {
		if !wardReqsExist || len(wardReqs) == 0 {
			return false
		}
		for _, req := range patientReqs {
			if !contains(wardReqs, req) {
				return false
			}
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
		fmt.Fprintf(os.Stderr, "Error encoding result: %v\n", err)
		os.Exit(1)
	}
}