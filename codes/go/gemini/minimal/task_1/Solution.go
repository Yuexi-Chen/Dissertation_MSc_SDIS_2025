package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func allocateBed(patient map[string]interface{}, wards []interface{}) map[string]interface{} {
	result := map[string]interface{}{
		"patient_id":                patient["id"],
		"assigned_ward":             nil,
		"assigned_bed":              nil,
		"assigned_satellite_hospital": nil,
	}

	for _, wardInterface := range wards {
		ward := wardInterface.(map[string]interface{})

		// Patient-Ward Matching
		match := true
		if ward["gender_restriction"] != nil && ward["gender_restriction"] != "Any" && ward["gender_restriction"] != patient["gender"] {
			match = false
		}

		if ward["age_restriction"] != nil {
			ageRestriction := ward["age_restriction"].([]interface{})
			minAge := int(ageRestriction[0].(float64))
			maxAge := int(ageRestriction[1].(float64))
			patientAge := int(patient["age"].(float64))
			if patientAge < minAge || patientAge > maxAge {
				match = false
			}
		}

		if ward["target_condition"] != nil && ward["target_condition"] != patient["condition"] {
			match = false
		}

		if ward["special_requirements"] != nil {
			wardRequirements := ward["special_requirements"].([]interface{})
			patientRequirements := patient["special_requirements"].([]interface{})

			for _, req := range wardRequirements {
				found := false
				for _, patientReq := range patientRequirements {
					if req == patientReq {
						found = true
						break
					}
				}
				if !found {
					match = false
					break
				}
			}
		}

		if match {
			// Step 1: REGULAR BEDS
			if ward["available_beds"] != nil {
				availableBeds := ward["available_beds"].([]interface{})
				if len(availableBeds) > 0 {
					assignedBed := int(availableBeds[0].(float64))

					// Remove the assigned bed from available beds
					newAvailableBeds := make([]interface{}, 0)
					for i := 1; i < len(availableBeds); i++ {
						newAvailableBeds = append(newAvailableBeds, availableBeds[i])
					}
					ward["available_beds"] = newAvailableBeds

					result["assigned_ward"] = ward["ward_name"]
					result["assigned_bed"] = assignedBed
					return result
				}
			}

			// Step 2: OVERFLOW BEDS
			if ward["overflow_capacity"] != nil {
				overflowCapacity := int(ward["overflow_capacity"].(float64))
				if overflowCapacity > 0 {
					result["assigned_ward"] = ward["ward_name"]
					result["assigned_bed"] = fmt.Sprintf("Overflow-%d", overflowCapacity)
					ward["overflow_capacity"] = overflowCapacity - 1
					return result
				}
			}

			// Step 3: SATELLITE HOSPITALS
			if ward["satellite_hospitals"] != nil {
				satelliteHospitals := ward["satellite_hospitals"].([]interface{})
				if len(satelliteHospitals) > 0 {
					result["assigned_satellite_hospital"] = satelliteHospitals[0]
					result["assigned_ward"] = nil
					result["assigned_bed"] = nil
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