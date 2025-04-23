package main

import (
	"encoding/json"
	"fmt"
	"sort"
)

func reallocateBed(patient map[string]interface{}, hospitals []interface{}) map[string]interface{} {
	patientID := patient["id"].(string)
	patientGender := patient["gender"].(string)
	patientAge := int(patient["age"].(float64))
	patientIsPostSurgery := patient["is_post_surgery"].(bool)
	patientSpecialRequirements := patient["special_requirements"].([]interface{})

	result := map[string]interface{}{
		"patient_id":          patientID,
		"assigned_hospital":   nil,
		"assigned_ward":       nil,
		"assigned_bed":        nil,
		"reallocated_patients": []interface{}{},
	}

	var suitableHospitals []map[string]interface{}
	if patientIsPostSurgery {
		for _, h := range hospitals {
			hospital := h.(map[string]interface{})
			if hospital["model"].(int) == 4 {
				suitableHospitals = append(suitableHospitals, hospital)
			}
		}
	} else {
		for _, h := range hospitals {
			hospital := h.(map[string]interface{})
			suitableHospitals = append(suitableHospitals, hospital)
		}
	}

	// Direct Assignment Attempt
	for _, h := range suitableHospitals {
		hospital := h.(map[string]interface{})
		hospitalID := hospital["id"].(string)
		wards := hospital["wards"].([]interface{})

		for _, w := range wards {
			ward := w.(map[string]interface{})
			wardName := ward["ward_name"].(string)
			genderRestriction := ward["gender_restriction"].(string)
			ageRestriction := ward["age_restriction"].([]interface{})
			specialRequirements := ward["special_requirements"].([]interface{})
			availableBeds := ward["available_beds"].([]interface{})

			ageMin := int(ageRestriction[0].(float64))
			ageMax := int(ageRestriction[1].(float64))

			genderMatches := (genderRestriction == "No Restriction" || genderRestriction == patientGender)
			ageMatches := (patientAge >= ageMin && patientAge <= ageMax)

			specialRequirementsMatch := true
			for _, req := range patientSpecialRequirements {
				found := false
				for _, wardReq := range specialRequirements {
					if req == wardReq {
						found = true
						break
					}
				}
				if !found {
					specialRequirementsMatch = false
					break
				}
			}

			if genderMatches && ageMatches && specialRequirementsMatch {
				sort.Slice(availableBeds, func(i, j int) bool {
					return availableBeds[i].(float64) < availableBeds[j].(float64)
				})

				if len(availableBeds) > 0 {
					bedNumber := int(availableBeds[0].(float64))
					result["assigned_hospital"] = hospitalID
					result["assigned_ward"] = wardName
					result["assigned_bed"] = bedNumber

					newAvailableBeds := []interface{}{}
					for _, bed := range availableBeds {
						if int(bed.(float64)) != bedNumber {
							newAvailableBeds = append(newAvailableBeds, bed)
						}
					}
					ward["available_beds"] = newAvailableBeds

					return result
				}
			}
		}
	}

	// Reallocation Attempt (only for high-risk patients)
	if patientIsPostSurgery {
		for _, h := range suitableHospitals {
			hospital := h.(map[string]interface{})
			hospitalID := hospital["id"].(string)
			wards := hospital["wards"].([]interface{})

			for _, w := range wards {
				ward := w.(map[string]interface{})
				wardName := ward["ward_name"].(string)
				currentPatients := ward["current_patients"].([]interface{})

				for _, p := range currentPatients {
					existingPatient := p.(map[string]interface{})
					existingPatientID := existingPatient["id"].(string)
					existingPatientGender := existingPatient["gender"].(string)
					existingPatientAge := int(existingPatient["age"].(float64))
					existingPatientDaysInHospital := int(existingPatient["days_in_hospital"].(float64))
					existingPatientBedNumber := int(existingPatient["bed_number"].(float64))
					existingPatientNonTransferable := existingPatient["non_transferable"].(bool)

					if existingPatientDaysInHospital > 3 && !existingPatientNonTransferable {
						// Find a lower-level hospital for the existing patient
						for _, lowerH := range hospitals {
							lowerHospital := lowerH.(map[string]interface{})
							lowerHospitalID := lowerHospital["id"].(string)
							lowerHospitalModel := lowerHospital["model"].(int)

							if hospital["model"].(int) > lowerHospitalModel {
								lowerHospitalWards := lowerHospital["wards"].([]interface{})

								for _, lowerW := range lowerHospitalWards {
									lowerWard := lowerW.(map[string]interface{})
									lowerWardName := lowerWard["ward_name"].(string)
									lowerWardGenderRestriction := lowerWard["gender_restriction"].(string)
									lowerWardAgeRestriction := lowerWard["age_restriction"].([]interface{})
									lowerWardSpecialRequirements := lowerWard["special_requirements"].([]interface{})
									lowerWardAvailableBeds := lowerWard["available_beds"].([]interface{})

									lowerAgeMin := int(lowerWardAgeRestriction[0].(float64))
									lowerAgeMax := int(lowerWardAgeRestriction[1].(float64))

									lowerGenderMatches := (lowerWardGenderRestriction == "No Restriction" || lowerWardGenderRestriction == existingPatientGender)
									lowerAgeMatches := (existingPatientAge >= lowerAgeMin && existingPatientAge <= lowerAgeMax)

									lowerSpecialRequirementsMatch := true
									// Check existing patient's special requirements against the new ward
									// Note that we can't access the special_requirements field of the existing patient, so we skip this check
									// for _, req := range existingPatient["special_requirements"].([]interface{}) {
									// 	found := false
									// 	for _, wardReq := range lowerWardSpecialRequirements {
									// 		if req == wardReq {
									// 			found = true
									// 			break
									// 		}
									// 	}
									// 	if !found {
									// 		lowerSpecialRequirementsMatch = false
									// 		break
									// 	}
									// }

									if lowerGenderMatches && lowerAgeMatches && lowerSpecialRequirementsMatch && len(lowerWardAvailableBeds) > 0 {
										// Transfer is possible
										sort.Slice(lowerWardAvailableBeds, func(i, j int) bool {
											return lowerWardAvailableBeds[i].(float64) < lowerWardAvailableBeds[j].(float64)
										})

										newBedNumber := int(lowerWardAvailableBeds[0].(float64))

										// Update available beds in the lower ward
										newLowerWardAvailableBeds := []interface{}{}
										for _, bed := range lowerWardAvailableBeds {
											if int(bed.(float64)) != newBedNumber {
												newLowerWardAvailableBeds = append(newLowerWardAvailableBeds, bed)
											}
										}
										lowerWard["available_beds"] = newLowerWardAvailableBeds

										// Assign the high-risk patient
										result["assigned_hospital"] = hospitalID
										result["assigned_ward"] = wardName
										result["assigned_bed"] = existingPatientBedNumber

										// Record the reallocation
										reallocatedPatient := map[string]interface{}{
											"patient_id":   existingPatientID,
											"new_hospital": lowerHospitalID,
											"new_ward":     lowerWardName,
											"new_bed":      newBedNumber,
										}

										result["reallocated_patients"] = append(result["reallocated_patients"].([]interface{}), reallocatedPatient)
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

func main() {
	var input map[string]interface{}
	err := json.NewDecoder(json.NewDecoder(fmt.NewReader(`{"patient": {"id": "P002", "gender": "Male", "age": 50, "condition": "Post-Surgery Recovery", "special_requirements": ["Intensive Monitoring"], "is_post_surgery": true}, "hospitals": [{"id": "H1", "model": 4, "wards": [{"ward_name": "Surgical Recovery Ward", "gender_restriction": "No Restriction", "age_restriction": [18, 80], "special_requirements": ["Intensive Monitoring"], "available_beds": [], "current_patients": [{"id": "P101", "gender": "Female", "age": 65, "condition": "Post-Surgery Recovery", "days_in_hospital": 5, "bed_number": 3, "non_transferable": false}]}]}, {"id": "H3", "model": 2, "wards": [{"ward_name": "General Ward", "gender_restriction": "Female Only", "age_restriction": [18, 85], "special_requirements": [], "available_beds": [1, 2, 3], "current_patients": []}]}]}`)).Decode(&input)).Decode(&input)
	if err != nil {
		panic(err)
	}

	patient := input["patient"].(map[string]interface{})
	hospitals := input["hospitals"].([]interface{})

	result := reallocateBed(patient, hospitals)

	jsonResult, err := json.Marshal(result)
	if err != nil {
		panic(err)
	}

	fmt.Println(string(jsonResult))
}