package main

import (
	"encoding/json"
	"fmt"
	"sort"
)

func reallocateBed(patient map[string]interface{}, hospitals []interface{}) map[string]interface{} {
	patientID := patient["id"].(string)
	isPostSurgery := patient["is_post_surgery"].(bool)
	patientGender := patient["gender"].(string)
	patientAge := patient["age"].(float64)
	patientSpecialRequirements := patient["special_requirements"].([]interface{})

	result := map[string]interface{}{
		"patient_id":         nil,
		"assigned_hospital":  nil,
		"assigned_ward":      nil,
		"assigned_bed":       nil,
		"reallocated_patients": []interface{}{},
	}

	var suitableHospitals []map[string]interface{}

	for _, h := range hospitals {
		hospital := h.(map[string]interface{})
		hospitalModel := hospital["model"].(float64)

		if isPostSurgery && hospitalModel == 4 {
			suitableHospitals = append(suitableHospitals, hospital)
		} else if !isPostSurgery && hospitalModel != 4 {
			suitableHospitals = append(suitableHospitals, hospital)
		}
	}

	if !isPostSurgery {
		tempSuitableHospitals := []map[string]interface{}{}
		for _, h := range hospitals {
			hospital := h.(map[string]interface{})
			hospitalModel := hospital["model"].(float64)

			if hospitalModel < 4 {
				tempSuitableHospitals = append(tempSuitableHospitals, hospital)
			}
		}

		if len(tempSuitableHospitals) > 0 {
			suitableHospitals = tempSuitableHospitals
		} else {
			suitableHospitals = []map[string]interface{}{}
			for _, h := range hospitals {
				hospital := h.(map[string]interface{})
				hospitalModel := hospital["model"].(float64)

				if hospitalModel == 4 {
					suitableHospitals = append(suitableHospitals, hospital)
				}
			}
		}

	} else {
		tempSuitableHospitals := []map[string]interface{}{}
		for _, h := range hospitals {
			hospital := h.(map[string]interface{})
			hospitalModel := hospital["model"].(float64)

			if hospitalModel == 4 {
				tempSuitableHospitals = append(tempSuitableHospitals, hospital)
			}
		}
		suitableHospitals = tempSuitableHospitals
	}

	for _, hospital := range suitableHospitals {
		hospitalID := hospital["id"].(string)
		wards := hospital["wards"].([]interface{})

		for _, w := range wards {
			ward := w.(map[string]interface{})
			wardName := ward["ward_name"].(string)
			genderRestriction := ward["gender_restriction"].(string)
			ageRestriction := ward["age_restriction"].([]interface{})
			minAge := ageRestriction[0].(float64)
			maxAge := ageRestriction[1].(float64)
			wardSpecialRequirements := ward["special_requirements"].([]interface{})
			availableBeds := ward["available_beds"].([]interface{})
			currentPatients := ward["current_patients"].([]interface{})

			isGenderMatch := false
			if genderRestriction == "No Restriction" {
				isGenderMatch = true
			} else if genderRestriction == "Female Only" && patientGender == "Female" {
				isGenderMatch = true
			} else if genderRestriction == "Male Only" && patientGender == "Male" {
				isGenderMatch = true
			}

			isAgeMatch := patientAge >= minAge && patientAge <= maxAge

			isSpecialRequirementsMatch := true
			for _, req := range patientSpecialRequirements {
				found := false
				for _, wardReq := range wardSpecialRequirements {
					if req == wardReq {
						found = true
						break
					}
				}
				if !found {
					isSpecialRequirementsMatch = false
					break
				}
			}

			if isGenderMatch && isAgeMatch && isSpecialRequirementsMatch {
				if len(availableBeds) > 0 {
					sort.Slice(availableBeds, func(i, j int) bool {
						return availableBeds[i].(float64) < availableBeds[j].(float64)
					})

					bedNumber := availableBeds[0].(float64)

					result["patient_id"] = patientID
					result["assigned_hospital"] = hospitalID
					result["assigned_ward"] = wardName
					result["assigned_bed"] = bedNumber
					result["reallocated_patients"] = []interface{}{}

					return result
				}
			}

		}
	}

	if isPostSurgery {
		for _, hospital := range suitableHospitals {
			hospitalID := hospital["id"].(string)
			wards := hospital["wards"].([]interface{})

			for _, w := range wards {
				ward := w.(map[string]interface{})
				wardName := ward["ward_name"].(string)
				genderRestriction := ward["gender_restriction"].(string)
				ageRestriction := ward["age_restriction"].([]interface{})
				minAge := ageRestriction[0].(float64)
				maxAge := ageRestriction[1].(float64)
				wardSpecialRequirements := ward["special_requirements"].([]interface{})
				currentPatients := ward["current_patients"].([]interface{})

				sort.Slice(currentPatients, func(i, j int) bool {
					patient1 := currentPatients[i].(map[string]interface{})
					patient2 := currentPatients[j].(map[string]interface{})

					days1 := patient1["days_in_hospital"].(float64)
					days2 := patient2["days_in_hospital"].(float64)

					bed1 := patient1["bed_number"].(float64)
					bed2 := patient2["bed_number"].(float64)

					if days1 != days2 {
						return days1 > days2
					}
					return bed1 < bed2
				})

				for _, cp := range currentPatients {
					currentPatient := cp.(map[string]interface{})
					currentPatientID := currentPatient["id"].(string)
					daysInHospital := currentPatient["days_in_hospital"].(float64)
					nonTransferable := currentPatient["non_transferable"].(bool)
					currentPatientBed := currentPatient["bed_number"].(float64)
					currentPatientGender := currentPatient["gender"].(string)
					currentPatientAge := currentPatient["age"].(float64)
					currentPatientSpecialRequirements := []interface{}{}
					if val, ok := currentPatient["special_requirements"]; ok {
						currentPatientSpecialRequirements = val.([]interface{})
					}

					if daysInHospital > 3 && !nonTransferable {

						for _, lowerLevelHospital := range hospitals {
							lowerLevelHospitalMap := lowerLevelHospital.(map[string]interface{})
							lowerLevelHospitalID := lowerLevelHospitalMap["id"].(string)
							lowerLevelHospitalModel := lowerLevelHospitalMap["model"].(float64)

							if lowerLevelHospitalModel < 4 {
								lowerLevelWards := lowerLevelHospitalMap["wards"].([]interface{})

								for _, lowerLevelWard := range lowerLevelWards {
									lowerLevelWardMap := lowerLevelWard.(map[string]interface{})
									lowerLevelWardName := lowerLevelWardMap["ward_name"].(string)
									lowerLevelGenderRestriction := lowerLevelWardMap["gender_restriction"].(string)
									lowerLevelAgeRestriction := lowerLevelWardMap["age_restriction"].([]interface{})
									lowerLevelMinAge := lowerLevelAgeRestriction[0].(float64)
									lowerLevelMaxAge := lowerLevelAgeRestriction[1].(float64)
									lowerLevelWardSpecialRequirements := lowerLevelWardMap["special_requirements"].([]interface{})
									lowerLevelAvailableBeds := lowerLevelWardMap["available_beds"].([]interface{})

									isGenderMatch := false
									if lowerLevelGenderRestriction == "No Restriction" {
										isGenderMatch = true
									} else if lowerLevelGenderRestriction == "Female Only" && currentPatientGender == "Female" {
										isGenderMatch = true
									} else if lowerLevelGenderRestriction == "Male Only" && currentPatientGender == "Male" {
										isGenderMatch = true
									}

									isAgeMatch := currentPatientAge >= lowerLevelMinAge && currentPatientAge <= lowerLevelMaxAge

									isSpecialRequirementsMatch := true
									for _, req := range currentPatientSpecialRequirements {
										found := false
										for _, wardReq := range lowerLevelWardSpecialRequirements {
											if req == wardReq {
												found = true
												break
											}
										}
										if !found {
											isSpecialRequirementsMatch = false
											break
										}
									}

									if isGenderMatch && isAgeMatch && isSpecialRequirementsMatch && len(lowerLevelAvailableBeds) > 0 {
										sort.Slice(lowerLevelAvailableBeds, func(i, j int) bool {
											return lowerLevelAvailableBeds[i].(float64) < lowerLevelAvailableBeds[j].(float64)
										})

										newBedNumber := lowerLevelAvailableBeds[0].(float64)

										reallocatedPatients := []interface{}{
											map[string]interface{}{
												"patient_id":   currentPatientID,
												"new_hospital": lowerLevelHospitalID,
												"new_ward":     lowerLevelWardName,
												"new_bed":      newBedNumber,
											},
										}

										result["patient_id"] = patientID
										result["assigned_hospital"] = hospitalID
										result["assigned_ward"] = wardName
										result["assigned_bed"] = currentPatientBed
										result["reallocated_patients"] = reallocatedPatients
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
	decoder := json.NewDecoder(
		//	strings.NewReader(`{"patient": {"id": "P002", "gender": "Male", "age": 50, "condition": "Post-Surgery Recovery", "special_requirements": ["Intensive Monitoring"], "is_post_surgery": true}, "hospitals": [{"id": "H1", "model": 4, "wards": [{"ward_name": "Surgical Recovery Ward", "gender_restriction": "No Restriction", "age_restriction": [18, 80], "special_requirements": ["Intensive Monitoring"], "available_beds": [], "current_patients": [{"id": "P101", "gender": "Female", "age": 65, "condition": "Post-Surgery Recovery", "days_in_hospital": 5, "bed_number": 3, "non_transferable": false}, {"id": "P102", "gender": "Male", "age": 70, "condition": "Critical Care", "days_in_hospital": 2, "bed_number": 4, "non_transferable": true}]}]}, {"id": "H3", "model": 2, "wards": [{"ward_name": "General Ward", "gender_restriction": "Female Only", "age_restriction": [18, 85], "special_requirements": [], "available_beds": [1, 2, 3], "current_patients": []}]}]}`))
		//strings.NewReader(`{"patient": {"id": "P003", "gender": "Female", "age": 35, "condition": "General Care", "special_requirements": [], "is_post_surgery": false}, "hospitals": [{"id": "H1", "model": 4, "wards": [{"ward_name": "Surgical Recovery Ward", "gender_restriction": "No Restriction", "age_restriction": [18, 80], "special_requirements": ["Intensive Monitoring"], "available_beds": [1, 2], "current_patients": []}]}, {"id": "H3", "model": 2, "wards": [{"ward_name": "General Ward", "gender_restriction": "Female Only", "age_restriction": [18, 85], "special_requirements": [], "available_beds": [1, 2, 3], "current_patients": []}]}]}`))
		//strings.NewReader(`{"patient": {"id": "P001", "gender": "Male", "age": 46, "condition": "Post-Surgery Recovery", "special_requirements": ["Intensive Monitoring"], "is_post_surgery": true}, "hospitals": [{"id": "H1", "model": 4, "wards": [{"ward_name": "Surgical Recovery Ward", "gender_restriction": "No Restriction", "age_restriction": [18, 80], "special_requirements": ["Intensive Monitoring"], "available_beds": [1, 2], "current_patients": [{"id": "P101", "gender": "Female", "age": 65, "condition": "Post-Surgery Recovery", "days_in_hospital": 5, "bed_number": 3, "non_transferable": false}, {"id": "P102", "gender": "Male", "age": 70, "condition": "Critical Care", "days_in_hospital": 2, "bed_number": 4, "non_transferable": true}]}]}, {"id": "H3", "model": 2, "wards": [{"ward_name": "General Ward", "gender_restriction": "Female Only", "age_restriction": [18, 85], "special_requirements": [], "available_beds": [1, 2, 3], "current_patients": []}]}]}`))
		nil)

	err := decoder.Decode(&input)
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