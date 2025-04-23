package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

func allocateBed(patient map[string]interface{}, wards []interface{}) map[string]interface{} {
	patientID := patient["id"].(string)
	patientGender := patient["gender"].(string)
	patientAge := int(patient["age"].(float64))
	patientCondition := patient["condition"].(string)
	patientSpecialRequirements := patient["special_requirements"].([]interface{})

	result := map[string]interface{}{
		"patient_id":               patientID,
		"assigned_ward":            nil,
		"assigned_bed":             nil,
		"assigned_satellite_hospital": nil,
	}

	for _, wardInterface := range wards {
		ward := wardInterface.(map[string]interface{})
		wardName := ward["ward_name"].(string)
		genderRestriction := ward["gender_restriction"].(string)
		ageRestriction := ward["age_restriction"].([]interface{})
		targetCondition := ward["target_condition"].(string)
		specialRequirements := ward["special_requirements"].([]interface{})
		availableBedsInterface := ward["available_beds"]
		overflowCapacity := int(ward["overflow_capacity"].(float64))
		satelliteHospitalsInterface := ward["satellite_hospitals"]

		// Ward Matching
		conditionMatch := targetCondition == patientCondition
		genderMatch := false
		if genderRestriction == "No Restriction" || genderRestriction == "No Gender Restriction" {
			genderMatch = true
		} else if genderRestriction == "Male Only" && patientGender == "Male" {
			genderMatch = true
		} else if genderRestriction == "Female Only" && patientGender == "Female" {
			genderMatch = true
		}

		ageMatch := false
		minAge := int(ageRestriction[0].(float64))
		maxAge := int(ageRestriction[1].(float64))
		if patientAge >= minAge && patientAge <= maxAge {
			ageMatch = true
		}

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

		if conditionMatch && genderMatch && ageMatch && specialRequirementsMatch {
			// Bed Allocation
			if availableBedsInterface != nil {
				availableBeds := availableBedsInterface.([]interface{})
				if len(availableBeds) > 0 {
					beds := make([]int, len(availableBeds))
					for i, bedInterface := range availableBeds {
						beds[i] = int(bedInterface.(float64))
					}
					sort.Ints(beds)
					assignedBed := beds[0]

					// Remove the assigned bed from available beds (simulating assignment)
					newAvailableBeds := []interface{}{}
					for _, bedInterface := range availableBedsInterface.([]interface{}) {
						bed := int(bedInterface.(float64))
						if bed != assignedBed {
							newAvailableBeds = append(newAvailableBeds, bed)
						}
					}
					ward["available_beds"] = newAvailableBeds

					result["assigned_ward"] = wardName
					result["assigned_bed"] = assignedBed
					return result
				}
			}

			// Overflow Beds
			if overflowCapacity > 0 {
				overflowAssigned := false
				for i := 1; i <= overflowCapacity; i++ {
					overflowBed := fmt.Sprintf("Overflow-%d", i)
					// Check if the overflow bed is already taken (not a perfect simulation, but good enough for this example)
					alreadyTaken := false
					//for _, existingAssignment := range existingAssignments { // Assuming you have a list of existing assignments
					//	if existingAssignment["assigned_ward"] == wardName && existingAssignment["assigned_bed"] == overflowBed {
					//		alreadyTaken = true
					//		break
					//	}
					//}
					if !alreadyTaken {
						result["assigned_ward"] = wardName
						result["assigned_bed"] = overflowBed
						overflowAssigned = true
						return result
					}
				}
				if !overflowAssigned {
				}
			}

			// Satellite Hospitals
			if satelliteHospitalsInterface != nil {
				satelliteHospitals := satelliteHospitalsInterface.([]interface{})
				if len(satelliteHospitals) > 0 {
					result["assigned_ward"] = nil
					result["assigned_bed"] = nil
					result["assigned_satellite_hospital"] = satelliteHospitals[0]
					return result
				}
			}
		}
	}

	return result
}

func main() {
	var input map[string]interface{}
	decoder := json.NewDecoder(os.Stdin)
	err := decoder.Decode(&input)
	if err != nil {
		fmt.Println("Error decoding JSON:", err)
		return
	}

	patient := input["patient"].(map[string]interface{})
	wards := input["wards"].([]interface{})

	result := allocateBed(patient, wards)

	jsonResult, err := json.Marshal(result)
	if err != nil {
		fmt.Println("Error encoding JSON:", err)
		return
	}

	fmt.Println(string(jsonResult))
}