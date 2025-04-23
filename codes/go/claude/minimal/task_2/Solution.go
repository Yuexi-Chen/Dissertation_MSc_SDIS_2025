package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func reallocateBed(patient map[string]interface{}, hospitals []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"patient_id":          nil,
		"assigned_hospital":   nil,
		"assigned_ward":       nil,
		"assigned_bed":        nil,
		"reallocated_patients": []interface{}{},
	}

	isHighRisk := patient["is_post_surgery"].(bool)

	// Direct Assignment
	for _, hospital := range hospitals {
		h := hospital.(map[string]interface{})
		if isHighRisk && h["model"].(float64) != 4 {
			continue
		}
		if !isHighRisk && h["model"].(float64) == 4 {
			continue
		}
		for _, ward := range h["wards"].([]interface{}) {
			w := ward.(map[string]interface{})
			if matchWardRequirements(patient, w) {
				availableBeds := w["available_beds"].([]interface{})
				if len(availableBeds) > 0 {
					result["patient_id"] = patient["id"]
					result["assigned_hospital"] = h["id"]
					result["assigned_ward"] = w["ward_name"]
					result["assigned_bed"] = availableBeds[0]
					return result
				}
			}
		}
	}

	// Reallocation for high-risk patients
	if isHighRisk {
		for _, hospital := range hospitals {
			h := hospital.(map[string]interface{})
			if h["model"].(float64) != 4 {
				continue
			}
			for _, ward := range h["wards"].([]interface{}) {
				w := ward.(map[string]interface{})
				if matchWardRequirements(patient, w) {
					currentPatients := w["current_patients"].([]interface{})
					for _, cp := range currentPatients {
						currentPatient := cp.(map[string]interface{})
						if currentPatient["days_in_hospital"].(float64) > 3 && !currentPatient["non_transferable"].(bool) {
							newHospital, newWard, newBed := findNewPlacement(currentPatient, hospitals)
							if newHospital != nil {
								result["patient_id"] = patient["id"]
								result["assigned_hospital"] = h["id"]
								result["assigned_ward"] = w["ward_name"]
								result["assigned_bed"] = currentPatient["bed_number"]
								result["reallocated_patients"] = []interface{}{
									map[string]interface{}{
										"patient_id":   currentPatient["id"],
										"new_hospital": newHospital["id"],
										"new_ward":     newWard["ward_name"],
										"new_bed":      newBed,
									},
								}
								return result
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
	genderRestriction := ward["gender_restriction"].(string)
	if genderRestriction != "No Restriction" && genderRestriction != patient["gender"].(string)+" Only" {
		return false
	}

	ageRestriction := ward["age_restriction"].([]interface{})
	patientAge := patient["age"].(float64)
	if patientAge < ageRestriction[0].(float64) || patientAge > ageRestriction[1].(float64) {
		return false
	}

	patientRequirements := patient["special_requirements"].([]interface{})
	wardRequirements := ward["special_requirements"].([]interface{})
	for _, req := range patientRequirements {
		if !contains(wardRequirements, req) {
			return false
		}
	}

	return true
}

func findNewPlacement(patient map[string]interface{}, hospitals []interface{}) (map[string]interface{}, map[string]interface{}, interface{}) {
	for _, hospital := range hospitals {
		h := hospital.(map[string]interface{})
		if h["model"].(float64) == 4 {
			continue
		}
		for _, ward := range h["wards"].([]interface{}) {
			w := ward.(map[string]interface{})
			if matchWardRequirements(patient, w) {
				availableBeds := w["available_beds"].([]interface{})
				if len(availableBeds) > 0 {
					return h, w, availableBeds[0]
				}
			}
		}
	}
	return nil, nil, nil
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
		Patient   map[string]interface{} `json:"patient"`
		Hospitals []interface{}          `json:"hospitals"`
	}

	decoder := json.NewDecoder(os.Stdin)
	if err := decoder.Decode(&input); err != nil {
		fmt.Println("Error decoding input:", err)
		return
	}

	result := reallocateBed(input.Patient, input.Hospitals)

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(result); err != nil {
		fmt.Println("Error encoding result:", err)
	}
}