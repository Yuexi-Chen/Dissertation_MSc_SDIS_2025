package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func reallocateBed(patient map[string]interface{}, hospitals []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"patient_id":         patient["id"],
		"assigned_hospital":  nil,
		"assigned_ward":      nil,
		"assigned_bed":       nil,
		"reallocated_patients": []map[string]interface{}{},
	}

	isHighRisk := patient["is_post_surgery"].(bool)

	for _, h := range hospitals {
		hospital := h.(map[string]interface{})
		model := int(hospital["model"].(float64))
		
		if isHighRisk && model != 4 {
			continue
		}

		for _, w := range hospital["wards"].([]interface{}) {
			ward := w.(map[string]interface{})
			
			if !matchWardRequirements(patient, ward) {
				continue
			}

			// Check for direct assignment
			for _, bed := range ward["available_beds"].([]interface{}) {
				result["assigned_hospital"] = hospital["id"]
				result["assigned_ward"] = ward["ward_name"]
				result["assigned_bed"] = bed
				return result
			}

			// Reallocation attempt for high-risk patients
			if isHighRisk {
				for _, p := range ward["current_patients"].([]interface{}) {
					currentPatient := p.(map[string]interface{})
					if int(currentPatient["days_in_hospital"].(float64)) > 3 && !currentPatient["non_transferable"].(bool) {
						// Try to find a new ward for the current patient
						for _, h2 := range hospitals {
							hospital2 := h2.(map[string]interface{})
							if hospital2["id"] == hospital["id"] {
								continue
							}

							for _, w2 := range hospital2["wards"].([]interface{}) {
								ward2 := w2.(map[string]interface{})
								if matchWardRequirements(currentPatient, ward2) {
									for _, bed2 := range ward2["available_beds"].([]interface{}) {
										// Reallocate the existing patient
										result["reallocated_patients"] = append(result["reallocated_patients"].([]map[string]interface{}), map[string]interface{}{
											"patient_id":  currentPatient["id"],
											"new_hospital": hospital2["id"],
											"new_ward":    ward2["ward_name"],
											"new_bed":     bed2,
										})

										// Assign the high-risk patient to the vacated bed
										result["assigned_hospital"] = hospital["id"]
										result["assigned_ward"] = ward["ward_name"]
										result["assigned_bed"] = currentPatient["bed_number"]
										return result
									}
								}
							}
						}
					}
				}
			}
		}
	}

	return result
}

func matchWardRequirements(patient map[string]interface{}, ward map[string]interface{}) bool {
	gender := patient["gender"].(string)
	age := int(patient["age"].(float64))
	specialRequirements := patient["special_requirements"].([]interface{})

	wardGender := ward["gender_restriction"].(string)
	if wardGender != "No Restriction" && wardGender != gender {
		return false
	}

	wardAgeRestriction := ward["age_restriction"].([]interface{})
	if age < int(wardAgeRestriction[0].(float64)) || age > int(wardAgeRestriction[1].(float64)) {
		return false
	}

	wardSpecialRequirements := ward["special_requirements"].([]interface{})
	for _, req := range specialRequirements {
		matched := false
		for _, wReq := range wardSpecialRequirements {
			if req == wReq {
				matched = true
				break
			}
		}
		if !matched {
			return false
		}
	}

	return true
}

func main() {
	var input struct {
		Patient   map[string]interface{} `json:"patient"`
		Hospitals []interface{}          `json:"hospitals"`
	}

	decoder := json.NewDecoder(os.Stdin)
	if err := decoder.Decode(&input); err != nil {
		fmt.Println("Error reading input:", err)
		return
	}

	result := reallocateBed(input.Patient, input.Hospitals)

	output, err := json.Marshal(result)
	if err != nil {
		fmt.Println("Error marshaling output:", err)
		return
	}

	fmt.Println(string(output))
}