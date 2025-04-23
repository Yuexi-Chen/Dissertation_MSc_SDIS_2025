package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
)

func reallocateBed(patient map[string]interface{}, hospitals []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"patient_id":         patient["id"],
		"assigned_hospital":  nil,
		"assigned_ward":      nil,
		"assigned_bed":       nil,
		"reallocated_patients": []interface{}{},
	}

	isHighRisk := patient["is_post_surgery"].(bool)

	// Step 1: Direct Assignment
	for _, hospitalInterface := range hospitals {
		hospital := hospitalInterface.(map[string]interface{})
		model := hospital["model"].(float64)

		if isHighRisk && model != 4 {
			continue
		}
		if !isHighRisk && model == 4 {
			continue
		}

		for _, wardInterface := range hospital["wards"].([]interface{}) {
			ward := wardInterface.(map[string]interface{})
			if !matchesWard(patient, ward) {
				continue
			}

			availableBeds := ward["available_beds"].([]interface{})
			if len(availableBeds) == 0 {
				continue
			}

			// Assign to the first available bed (lowest number)
			sort.Slice(availableBeds, func(i, j int) bool {
				return availableBeds[i].(float64) < availableBeds[j].(float64)
			})

			result["assigned_hospital"] = hospital["id"]
			result["assigned_ward"] = ward["ward_name"]
			result["assigned_bed"] = availableBeds[0]

			return result
		}
	}

	// Step 2: Reallocation for High-Risk Patients
	if isHighRisk {
		for _, hospitalInterface := range hospitals {
			hospital := hospitalInterface.(map[string]interface{})
			if hospital["model"].(float64) != 4 {
				continue
			}

			for _, wardInterface := range hospital["wards"].([]interface{}) {
				ward := wardInterface.(map[string]interface{})
				if !matchesWard(patient, ward) {
					continue
				}

				currentPatients := ward["current_patients"].([]interface{})
				sort.Slice(currentPatients, func(i, j int) bool {
					p1 := currentPatients[i].(map[string]interface{})
					p2 := currentPatients[j].(map[string]interface{})
					if p1["days_in_hospital"].(float64) == p2["days_in_hospital"].(float64) {
						return p1["bed_number"].(float64) < p2["bed_number"].(float64)
					}
					return p1["days_in_hospital"].(float64) > p2["days_in_hospital"].(float64)
				})

				for _, patientInterface := range currentPatients {
					patientToMove := patientInterface.(map[string]interface{})
					if patientToMove["days_in_hospital"].(float64) <= 3 || patientToMove["non_transferable"].(bool) {
						continue
					}

					newHospital, newWard, newBed := findReallocation(patientToMove, hospitals)
					if newHospital != nil {
						result["assigned_hospital"] = hospital["id"]
						result["assigned_ward"] = ward["ward_name"]
						result["assigned_bed"] = patientToMove["bed_number"]

						reallocatedPatient := map[string]interface{}{
							"patient_id":   patientToMove["id"],
							"new_hospital": newHospital,
							"new_ward":     newWard,
							"new_bed":      newBed,
						}
						result["reallocated_patients"] = append(result["reallocated_patients"].([]interface{}), reallocatedPatient)

						return result
					}
				}
			}
		}
	}

	return result
}

func matchesWard(patient map[string]interface{}, ward map[string]interface{}) bool {
	patientGender := patient["gender"].(string)
	patientAge := patient["age"].(float64)
	patientSpecialRequirements := patient["special_requirements"].([]interface{})

	wardGenderRestriction := ward["gender_restriction"].(string)
	wardAgeRestriction := ward["age_restriction"].([]interface{})
	wardSpecialRequirements := ward["special_requirements"].([]interface{})

	// Gender Restriction
	if wardGenderRestriction == "Male Only" && patientGender != "Male" {
		return false
	}
	if wardGenderRestriction == "Female Only" && patientGender != "Female" {
		return false
	}

	// Age Restriction
	if patientAge < wardAgeRestriction[0].(float64) || patientAge > wardAgeRestriction[1].(float64) {
		return false
	}

	// Special Requirements
	wardSpecialRequirementsMap := make(map[string]bool)
	for _, req := range wardSpecialRequirements {
		wardSpecialRequirementsMap[req.(string)] = true
	}
	for _, req := range patientSpecialRequirements {
		if !wardSpecialRequirementsMap[req.(string)] {
			return false
		}
	}

	return true
}

func findReallocation(patient map[string]interface{}, hospitals []interface{}) (interface{}, interface{}, interface{}) {
	patientGender := patient["gender"].(string)
	patientAge := patient["age"].(float64)
	patientSpecialRequirements := patient["special_requirements"].([]interface{})

	for _, hospitalInterface := range hospitals {
		hospital := hospitalInterface.(map[string]interface{})
		if hospital["model"].(float64) == 4 {
			continue
		}

		for _, wardInterface := range hospital["wards"].([]interface{}) {
			ward := wardInterface.(map[string]interface{})
			if !matchesWard(patient, ward) {
				continue
			}

			availableBeds := ward["available_beds"].([]interface{})
			if len(availableBeds) == 0 {
				continue
			}

			sort.Slice(availableBeds, func(i, j int) bool {
				return availableBeds[i].(float64) < availableBeds[j].(float64)
			})

			return hospital["id"], ward["ward_name"], availableBeds[0]
		}
	}

	return nil, nil, nil
}

func main() {
	var input struct {
		Patient   map[string]interface{} `json:"patient"`
		Hospitals []interface{}          `json:"hospitals"`
	}

	decoder := json.NewDecoder(os.Stdin)
	err := decoder.Decode(&input)
	if err != nil {
		fmt.Println("Error decoding JSON:", err)
		return
	}

	result := reallocateBed(input.Patient, input.Hospitals)

	output, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		fmt.Println("Error encoding JSON:", err)
		return
	}

	fmt.Println(string(output))
}