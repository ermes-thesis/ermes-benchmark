package main

import (
	"encoding/json"
	lib "ermes_client_library"
	"fmt"
	"log"
	"os"
)

type Config struct {
	CollectionPositions map[string]int                 `json:"collection_positions"`
	UserAssignments     map[string]int                 `json:"user_assignments"`
	UserCollectionMap   map[string][]map[string]string `json:"user_collection_map"`
}

var geolocations = map[int]string{
	50: "IT/Rome/TorVergata",
	51: "IT/Rome/LaSapienza",
	52: "IT/Milan/Bocconi",
	53: "IT/Milan/UNIMI",
	54: "IT/Milan/POLIMI",
	55: "IT/Rome",
	56: "IT/Milan",
	57: "IT",
}

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Missing config file argument")
	}

	var conf Config

	confBytes, err := os.ReadFile(os.Args[1])
	if err != nil {
		log.Fatalf("Error reading config file: %v", err)
	}
	err = json.Unmarshal(confBytes, &conf)
	if err != nil {
		log.Fatalf("Error unmarshalling config file: %v", err)
	}

	// Call the library setup

	confFile := "config.yaml"

	fmt.Println("Hello world !")

	errSetup := lib.SetupClientLibrary(uint64(0), "10.10.101.50", confFile)

	if errSetup != nil {
		fmt.Fprintf(os.Stderr, "Error when setting up the client library: %v\n", errSetup)
	} else {

		fmt.Println("Library set up correctly!")

	}

	for collectionName, position := range conf.CollectionPositions {
		node := "10.10.101." + fmt.Sprint(position) + ":12345"
		lib.MoveToNewNode(node)
		fmt.Println("Creating collection", collectionName, "at node", node)

		body, code, err := lib.ExecuteFunction(
			"createCollection",
			"",
			map[string]string{
				"name":        collectionName,
				"consistency": "sequential",
				"geolocation": geolocations[position],
			},
			map[string]map[string]string{},
			"",
		)
		fmt.Println(code, string(body), err)

		body, code, err = lib.ExecuteFunction(
			"writeCollection",
			"",
			map[string]string{
				"data": "first write",
			},
			map[string]map[string]string{
				"query": {
					"name": collectionName,
				},
			},
			geolocations[position],
		)

		fmt.Println(code, string(body), err)
	}

}
