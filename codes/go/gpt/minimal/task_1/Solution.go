package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func allocateBed(patient map[string]interface{}, wards []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"patient_id":               patient["id"],
		"assigned_ward":            nil,
		"assigned_bed":             nil,
		"assigned_satellite_hospital": nil,
	}

	// Extract patient attributes
	patientGender := patient["gender"].(string)
	patientAge := int(patient["age"].(float64))
	patientCondition := patient["condition"].(string)
	patientSpecialRequirements := patient["special_requirements"].([]interface{})

	for _, w := range wards {
		ward := w.(map[string]interface{})
		
		// Check ward criteria: gender, age, condition, special requirements
		wardGenderRestriction := ward["gender_restriction"].(string)
		wardAgeRestriction := ward["age_restriction"].([]interface{})
		wardTargetCondition := ward["target_condition"].(string)
		wardSpecialRequirements := ward["special_requirements"].([]interface{})

		// Gender check
		if wardGenderRestriction != "Any" && wardGenderRestriction != patientGender+" Only" {
			continue
		}

		// Age check
		if patientAge < int(wardAgeRestriction[0].(float64)) || patientAge > int(wardAgeRestriction[1].(float64)) {
			continue
		}

		// Condition check
		if wardTargetCondition != patientCondition {
			continue
		}

		// Special requirements check
		requirementsMatch := true
		for _, req := range wardSpecialRequirements {
			if !contains(patientSpecialRequirements, req) {
				requirementsMatch = false
				break
			}
		}
		if !requirementsMatch {
			continue
		}

		// Bed allocation
		availableBeds := ward["available_beds"].([]interface{})
		if len(availableBeds) > 0 {
			// Assign lowest numbered available bed
			result["assigned_ward"] = ward["ward_name"]
			result["assigned_bed"] = int(availableBeds[0].(float64))
			return result
		}

		// Check overflow capacity
		overflowCapacity := int(ward["overflow_capacity"].(float64))
		if overflowCapacity > 0 {
			result["assigned_ward"] = ward["ward_name"]
			result["assigned_bed"] = fmt.Sprintf("Overflow-1")
			return result
		}

		// Check satellite hospitals
		satelliteHospitals := ward["satellite_hospitals"].([]interface{})
		if len(satelliteHospitals) > 0 {
			result["assigned_ward"] = nil
			result["assigned_bed"] = nil
			result["assigned_satellite_hospital"] = satelliteHospitals[0].(string)
			return result
		}
	}

	return result
}

func contains(slice []interface{}, item interface{}) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func main() {
	decoder := json.NewDecoder(os.Stdin)
	var input struct {
		Patient map[string]interface{} `json:"patient"`
		Wards   []interface{}          `json:"wards"`
	}
	if err := decoder.Decode(&input); err != nil {
		fmt.Println("Error decoding JSON:", err)
		return
	}

	result := allocateBed(input.Patient, input.Wards)

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(result); err != nil {
		fmt.Println("Error encoding JSON:", err)
	}
}