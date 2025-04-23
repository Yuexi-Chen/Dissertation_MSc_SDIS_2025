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

	var preferredHospitals []interface{}
	if isHighRisk {
		for _, h := range hospitals {
			hospital := h.(map[string]interface{})
			if hospital["model"].(float64) == 4 {
				preferredHospitals = append(preferredHospitals, hospital)
			}
		}
	} else {
		for _, h := range hospitals {
			hospital := h.(map[string]interface{})
			if hospital["model"].(float64) < 4 {
				preferredHospitals = append(preferredHospitals, hospital)
			}
		}
		if len(preferredHospitals) == 0 {
			for _, h := range hospitals {
				hospital := h.(map[string]interface{})
				if hospital["model"].(float64) == 4 {
					preferredHospitals = append(preferredHospitals, hospital)
				}
			}
		}
	}

	for _, h := range preferredHospitals {
		hospital := h.(map[string]interface{})
		for _, w := range hospital["wards"].([]interface{}) {
			ward := w.(map[string]interface{})
			if isWardSuitable(patient, ward) {
				if len(ward["available_beds"].([]interface{})) > 0 {
					assignedBed := ward["available_beds"].([]interface{})[0].(float64)
					result["assigned_hospital"] = hospital["id"]
					result["assigned_ward"] = ward["ward_name"]
					result["assigned_bed"] = assignedBed
					return result
				}
			}
		}
	}

	if isHighRisk {
		for _, h := range preferredHospitals {
			hospital := h.(map[string]interface{})
			for _, w := range hospital["wards"].([]interface{}) {
				ward := w.(map[string]interface{})
				if isWardSuitable(patient, ward) {
					for _, cp := range ward["current_patients"].([]interface{}) {
						currentPatient := cp.(map[string]interface{})
						if currentPatient["days_in_hospital"].(float64) > 3 && !currentPatient["non_transferable"].(bool) {
							for _, lh := range hospitals {
								lHospital := lh.(map[string]interface{})
								if lHospital["model"].(float64) < 4 {
									for _, lw := range lHospital["wards"].([]interface{}) {
										lWard := lw.(map[string]interface{})
										if isWardSuitable(currentPatient, lWard) {
											if len(lWard["available_beds"].([]interface{})) > 0 {
												assignedBed := currentPatient["bed_number"]
												result["assigned_hospital"] = hospital["id"]
												result["assigned_ward"] = ward["ward_name"]
												result["assigned_bed"] = assignedBed
												newBed := lWard["available_beds"].([]interface{})[0].(float64)

												result["reallocated_patients"] = append(result["reallocated_patients"].([]map[string]interface{}), map[string]interface{}{
													"patient_id":  currentPatient["id"],
													"new_hospital": lHospital["id"],
													"new_ward":     lWard["ward_name"],
													"new_bed":      newBed,
												})
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
		}
	}

	return result
}

func isWardSuitable(patient map[string]interface{}, ward map[string]interface{}) bool {
	if ward["gender_restriction"] != "No Restriction" && ward["gender_restriction"] != patient["gender"] {
		return false
	}
	age := patient["age"].(float64)
	ageRestriction := ward["age_restriction"].([]interface{})
	if age < ageRestriction[0].(float64) || age > ageRestriction[1].(float64) {
		return false
	}
	for _, req := range patient["special_requirements"].([]interface{}) {
		found := false
		for _, wReq := range ward["special_requirements"].([]interface{}) {
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
		fmt.Println("Error encoding output:", err)
		return
	}

	fmt.Println(string(output))
}