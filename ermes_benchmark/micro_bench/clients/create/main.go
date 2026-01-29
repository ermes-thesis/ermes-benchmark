package main

import (
	"encoding/json"
	ermes "ermes_client_library"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
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
	logger, err := logger.NewLogger(logger.Config{
		Level:  logger.InfoLevel,
		Format: "text",
		Output: &logger.LogFile{
			LogDir:      "results",
			LogFileName: "create.log",
		},
	})
	if err != nil {
		log.Fatalf("Error creating logger: %v", err)
	}
	defer logger.Close()

	if len(os.Args) < 3 {
		logger.Error("Missing config file argument")
		return
	}

	var conf Config

	confBytes, err := os.ReadFile(os.Args[1])
	if err != nil {
		logger.Error("Error reading config file: %v", err)
		return
	}
	err = json.Unmarshal(confBytes, &conf)
	if err != nil {
		logger.Error("Error unmarshalling config file: %v", err)
		return
	}

	consistency := os.Args[2]

	numAccesses := "1"
	if len(os.Args) > 3 {
		numAccesses = os.Args[3]
	}
	logger.Infof("Passing 'accesses' parameter to function: %s\n", numAccesses)

	// Call the library setup

	confFile := "config.yaml"

	logger.Info("Hello world !")

	client, errSetup := ermes.SetupClientLibrary(uint64(2000), "10.10.101.50", confFile)
	if errSetup != nil {
		logger.Error("Error when setting up the client library: %v\n", errSetup)
		return
	}
	logger.Info("Library set up correctly!")

	for collectionName, position := range conf.CollectionPositions {
		node := "10.10.101." + fmt.Sprint(position) + ":12345"
		client.MoveToNewNode(node)
		logger.Info("Creating collection", collectionName, "at node", node)

		body, code, err := client.ExecuteFunction(
			"createCollection",
			"",
			map[string]string{
				"name":        collectionName,
				"consistency": consistency,
				"geolocation": geolocations[position],
			},
			map[string]map[string]string{},
			"",
		)
		logger.Infof("[create] Status %d, %s, error: %v", code, string(body), err)
	}

	time.Sleep(1 * time.Second)

	for collectionName, position := range conf.CollectionPositions {
		node := "10.10.101." + fmt.Sprint(position) + ":12345"
		client.MoveToNewNode(node)
		body, code, err := client.ExecuteFunction(
			"writeCollection",
			"",
			map[string]string{
				"data":     "first write",
				"accesses": numAccesses,
			},
			map[string]map[string]string{
				"query": {
					"name": collectionName,
				},
			},
			geolocations[position],
		)

		logger.Infof("[write] Status %d, %s, error: %v", code, string(body), err)
		time.Sleep(5 * time.Millisecond)
	}

}
