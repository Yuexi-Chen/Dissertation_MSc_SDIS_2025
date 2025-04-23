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
	patientGender := patient["gender"].(string)
	patientAge := patient["age"].(float64)
	patientSpecialReqs := patient["special_requirements"].([]interface{})

	// Direct Assignment
	for _, hospital := range hospitals {
		h := hospital.(map[string]interface{})
		hospitalModel := h["model"].(float64)

		if isHighRisk && hospitalModel != 4 {
			continue
		}

		if !isHighRisk && hospitalModel == 4 {
			continue
		}

		for _, ward := range h["wards"].([]interface{}) {
			w := ward.(map[string]interface{})

			if !matchWardRequirements(w, patientGender, patientAge, patientSpecialReqs) {
				continue
			}

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

	// Reallocation for high-risk patients
	if isHighRisk {
		for _, hospital := range hospitals {
			h := hospital.(map[string]interface{})
			if h["model"].(float64) != 4 {
				continue
			}

			for _, ward := range h["wards"].([]interface{}) {
				w := ward.(map[string]interface{})

				if !matchWardRequirements(w, patientGender, patientAge, patientSpecialReqs) {
					continue
				}

				currentPatients := w["current_patients"].([]interface{})
				for _, currentPatient := range currentPatients {
					cp := currentPatient.(map[string]interface{})
					if cp["days_in_hospital"].(float64) <= 3 || cp["non_transferable"].(bool) {
						continue
					}

					for _, lowerHospital := range hospitals {
						lh := lowerHospital.(map[string]interface{})
						if lh["model"].(float64) >= 4 {
							continue
						}

						for _, lowerWard := range lh["wards"].([]interface{}) {
							lw := lowerWard.(map[string]interface{})

							if !matchWardRequirements(lw, cp["gender"].(string), cp["age"].(float64), []interface{}{}) {
								continue
							}

							availableBeds := lw["available_beds"].([]interface{})
							if len(availableBeds) > 0 {
								result["patient_id"] = patient["id"]
								result["assigned_hospital"] = h["id"]
								result["assigned_ward"] = w["ward_name"]
								result["assigned_bed"] = cp["bed_number"]

								reallocation := map[string]interface{}{
									"patient_id":   cp["id"],
									"new_hospital": lh["id"],
									"new_ward":     lw["ward_name"],
									"new_bed":      availableBeds[0],
								}
								result["reallocated_patients"] = []interface{}{reallocation}
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

func matchWardRequirements(ward map[string]interface{}, gender string, age float64, specialReqs []interface{}) bool {
	genderRestriction := ward["gender_restriction"].(string)
	if genderRestriction != "No Restriction" && genderRestriction != gender+" Only" {
		return false
	}

	ageRestriction := ward["age_restriction"].([]interface{})
	if age < ageRestriction[0].(float64) || age > ageRestriction[1].(float64) {
		return false
	}

	wardSpecialReqs := ward["special_requirements"].([]interface{})
	for _, req := range specialReqs {
		found := false
		for _, wardReq := range wardSpecialReqs {
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
	var input map[string]interface{}
	err := json.NewDecoder(os.Stdin).Decode(&input)
	if err != nil {
		fmt.Println("Error reading input:", err)
		return
	}

	patient := input["patient"].(map[string]interface{})
	hospitals := input["hospitals"].([]interface{})

	result := reallocateBed(patient, hospitals)
	json.NewEncoder(os.Stdout).Encode(result)
}