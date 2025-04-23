package main

import (
	"encoding/json"
	"fmt"
	"sort"
)

func allocateBed(patient map[string]interface{}, wards []interface{}) map[string]interface{} {
	patientID := patient["id"].(string)
	patientGender := patient["gender"].(string)
	patientAge := int(patient["age"].(float64))
	patientCondition := patient["condition"].(string)
	patientSpecialRequirements, ok := patient["special_requirements"].([]interface{})
	if !ok {
		patientSpecialRequirements = []interface{}{}
	}

	result := map[string]interface{}{
		"patient_id":                 patientID,
		"assigned_ward":              nil,
		"assigned_bed":               nil,
		"assigned_satellite_hospital": nil,
	}

	for _, wardInterface := range wards {
		ward := wardInterface.(map[string]interface{})
		wardName := ward["ward_name"].(string)
		genderRestriction := ward["gender_restriction"].(string)
		ageRestriction := ward["age_restriction"].([]interface{})
		minAge := int(ageRestriction[0].(float64))
		maxAge := int(ageRestriction[1].(float64))
		targetCondition := ward["target_condition"].(string)
		wardSpecialRequirements, ok := ward["special_requirements"].([]interface{})
		if !ok {
			wardSpecialRequirements = []interface{}{}
		}
		availableBedsInterface, ok := ward["available_beds"].([]interface{})
		if !ok {
			availableBedsInterface = []interface{}{}
		}
		overflowCapacity := int(ward["overflow_capacity"].(float64))
		satelliteHospitalsInterface, ok := ward["satellite_hospitals"].([]interface{})
		if !ok {
			satelliteHospitalsInterface = []interface{}{}
		}

		// Ward Matching
		conditionMatch := patientCondition == targetCondition
		genderMatch := false
		if genderRestriction == "No Restriction" || genderRestriction == "No Gender Restriction" {
			genderMatch = true
		} else if genderRestriction == "Male Only" && patientGender == "Male" {
			genderMatch = true
		} else if genderRestriction == "Female Only" && patientGender == "Female" {
			genderMatch = true
		}
		ageMatch := patientAge >= minAge && patientAge <= maxAge
		specialRequirementsMatch := true
		patientReqMap := make(map[interface{}]bool)
		for _, req := range patientSpecialRequirements {
			patientReqMap[req] = true
		}
		for _, req := range patientSpecialRequirements {
			found := false
			for _, wardReq := range wardSpecialRequirements {
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
			// Regular Bed Allocation
			availableBeds := make([]int, 0)
			for _, bedInterface := range availableBedsInterface {
				availableBeds = append(availableBeds, int(bedInterface.(float64)))
			}

			if len(availableBeds) > 0 {
				sort.Ints(availableBeds)
				assignedBed := availableBeds[0]
				result["assigned_ward"] = wardName
				result["assigned_bed"] = assignedBed
				return result
			}

			// Overflow Bed Allocation
			if overflowCapacity > 0 {
				result["assigned_ward"] = wardName
				result["assigned_bed"] = fmt.Sprintf("Overflow-1")
				return result
			}

			// Satellite Hospital Allocation
			if len(satelliteHospitalsInterface) > 0 {
				satelliteHospitals := make([]string, 0)
				for _, hospitalInterface := range satelliteHospitalsInterface {
					satelliteHospitals = append(satelliteHospitals, hospitalInterface.(string))
				}
				result["assigned_satellite_hospital"] = satelliteHospitals[0]
				result["assigned_ward"] = nil
				result["assigned_bed"] = nil
				return result
			}
		}
	}

	return result
}

func main() {
	var input map[string]interface{}
	decoder := json.NewDecoder(SystemIn{})
	err := decoder.Decode(&input)
	if err != nil {
		panic(err)
	}

	patient := input["patient"].(map[string]interface{})
	wards := input["wards"].([]interface{})

	result := allocateBed(patient, wards)

	jsonResult, err := json.Marshal(result)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(jsonResult))
}

type SystemIn struct{}

func (s SystemIn) Read(p []byte) (n int, err error) {
	return fmt.Scan(string(p))
}