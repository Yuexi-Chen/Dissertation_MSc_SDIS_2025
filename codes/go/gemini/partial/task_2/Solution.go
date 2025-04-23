package main

import (
	"encoding/json"
	"fmt"
	"sort"
)

func reallocateBed(patient map[string]interface{}, hospitals []interface{}) map[string]interface{} {
	patientID := patient["id"].(string)
	isPostSurgery := patient["is_post_surgery"].(bool)
	gender := patient["gender"].(string)
	age := int(patient["age"].(float64))
	specialRequirements := patient["special_requirements"].([]interface{})

	result := map[string]interface{}{
		"patient_id":          patientID,
		"assigned_hospital":   nil,
		"assigned_ward":     nil,
		"assigned_bed":        nil,
		"reallocated_patients": []interface{}{},
	}

	var preferredHospitalModels []int
	if isPostSurgery {
		preferredHospitalModels = []int{4}
	} else {
		preferredHospitalModels = []int{1, 2, 3, 4}
	}

	for _, model := range preferredHospitalModels {
		for _, hospitalInterface := range hospitals {
			hospital := hospitalInterface.(map[string]interface{})
			hospitalID := hospital["id"].(string)
			hospitalModel := int(hospital["model"].(float64))

			if hospitalModel != model {
				continue
			}

			wards := hospital["wards"].([]interface{})

			// Direct Assignment Attempt
			for _, wardInterface := range wards {
				ward := wardInterface.(map[string]interface{})
				wardName := ward["ward_name"].(string)
				genderRestriction := ward["gender_restriction"].(string)
				ageRestriction := ward["age_restriction"].([]interface{})
				minAge := int(ageRestriction[0].(float64))
				maxAge := int(ageRestriction[1].(float64))
				wardSpecialRequirements := ward["special_requirements"].([]interface{})

				if genderRestriction != "No Restriction" && genderRestriction != gender {
					continue
				}

				if age < minAge || age > maxAge {
					continue
				}

				allRequirementsMet := true
				for _, requirement := range specialRequirements {
					found := false
					for _, wardRequirement := range wardSpecialRequirements {
						if requirement == wardRequirement {
							found = true
							break
						}
					}
					if !found {
						allRequirementsMet = false
						break
					}
				}
				if !allRequirementsMet {
					continue
				}

				availableBedsInterface := ward["available_beds"].([]interface{})
				availableBeds := make([]int, len(availableBedsInterface))
				for i, bedInterface := range availableBedsInterface {
					availableBeds[i] = int(bedInterface.(float64))
				}
				sort.Ints(availableBeds)

				if len(availableBeds) > 0 {
					bedNumber := availableBeds[0]
					result["assigned_hospital"] = hospitalID
					result["assigned_ward"] = wardName
					result["assigned_bed"] = bedNumber
					return result
				}
			}

			// Reallocation Attempt (Only for High-Risk Patients in Model 4 Hospitals)
			if isPostSurgery && model == 4 {
				for _, wardInterface := range wards {
					ward := wardInterface.(map[string]interface{})
					wardName := ward["ward_name"].(string)
					currentPatientsInterface := ward["current_patients"].([]interface{})

					for _, patientOnBedInterface := range currentPatientsInterface {
						patientOnBed := patientOnBedInterface.(map[string]interface{})
						existingPatientID := patientOnBed["id"].(string)
						daysInHospital := int(patientOnBed["days_in_hospital"].(float64))
						nonTransferable := patientOnBed["non_transferable"].(bool)
						bedNumber := int(patientOnBed["bed_number"].(float64))
						existingPatientGender := patientOnBed["gender"].(string)
						existingPatientAge := int(patientOnBed["age"].(float64))

						if daysInHospital <= 3 || nonTransferable {
							continue
						}

						// Find a suitable lower-level hospital for the existing patient
						for _, lowerLevelHospitalInterface := range hospitals {
							lowerLevelHospital := lowerLevelHospitalInterface.(map[string]interface{})
							lowerLevelHospitalID := lowerLevelHospital["id"].(string)
							lowerLevelHospitalModel := int(lowerLevelHospital["model"].(float64))

							if lowerLevelHospitalModel >= 4 {
								continue
							}

							lowerLevelWards := lowerLevelHospital["wards"].([]interface{})
							for _, lowerLevelWardInterface := range lowerLevelWards {
								lowerLevelWard := lowerLevelWardInterface.(map[string]interface{})
								lowerLevelWardName := lowerLevelWard["ward_name"].(string)
								lowerLevelGenderRestriction := lowerLevelWard["gender_restriction"].(string)
								lowerLevelAgeRestriction := lowerLevelWard["age_restriction"].([]interface{})
								lowerLevelMinAge := int(lowerLevelAgeRestriction[0].(float64))
								lowerLevelMaxAge := int(lowerLevelAgeRestriction[1].(float64))
								lowerLevelWardSpecialRequirements := lowerLevelWard["special_requirements"].([]interface{})

								if lowerLevelGenderRestriction != "No Restriction" && lowerLevelGenderRestriction != existingPatientGender {
									continue
								}

								if existingPatientAge < lowerLevelMinAge || existingPatientAge > lowerLevelMaxAge {
									continue
								}

								existingPatientSpecialRequirements, ok := patientOnBed["special_requirements"].([]interface{})
								if !ok {
									existingPatientSpecialRequirements = []interface{}{}
								}

								lowerLevelAllRequirementsMet := true
								for _, requirement := range existingPatientSpecialRequirements {
									found := false
									for _, wardRequirement := range lowerLevelWardSpecialRequirements {
										if requirement == wardRequirement {
											found = true
											break
										}
									}
									if !found {
										lowerLevelAllRequirementsMet = false
										break
									}
								}
								if !lowerLevelAllRequirementsMet {
									continue
								}

								lowerLevelAvailableBedsInterface := lowerLevelWard["available_beds"].([]interface{})
								lowerLevelAvailableBeds := make([]int, len(lowerLevelAvailableBedsInterface))
								for i, bedInterface := range lowerLevelAvailableBedsInterface {
									lowerLevelAvailableBeds[i] = int(bedInterface.(float64))
								}
								sort.Ints(lowerLevelAvailableBeds)

								if len(lowerLevelAvailableBeds) > 0 {
									lowerLevelBedNumber := lowerLevelAvailableBeds[0]

									result["assigned_hospital"] = hospitalID
									result["assigned_ward"] = wardName
									result["assigned_bed"] = bedNumber

									reallocatedPatient := map[string]interface{}{
										"patient_id":   existingPatientID,
										"new_hospital": lowerLevelHospitalID,
										"new_ward":     lowerLevelWardName,
										"new_bed":      lowerLevelBedNumber,
									}

									result["reallocated_patients"] = []interface{}{reallocatedPatient}
									return result
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
	decoder := json.NewDecoder(stdin)
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