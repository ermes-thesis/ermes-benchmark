package main

import (
	"encoding/json"
	lib "ermes_client_library"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	CollectionPositions map[string]int                 `json:"collection_positions"`
	UserAssignments     map[string]int                 `json:"user_assignments"`
	UserCollectionMap   map[string][]map[string]string `json:"user_collection_map"`
}

func main() {

	if len(os.Args) < 3 {
		log.Fatal("Missing required arguments")
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

	userId := os.Args[2]

	// Call the library setup

	confFile := "config.yaml"

	fmt.Println("Hello world !")

	nodeAddress := "10.10.101." + fmt.Sprint(conf.UserAssignments[userId]) + ":12345"

	id, err := strconv.Atoi(strings.Split(userId, "_")[1])
	if err != nil {
		log.Fatalf("Error converting user id to int")
	}
	fmt.Printf("Node address: %s", nodeAddress)
	errSetup := lib.SetupClientLibrary(uint64(id), nodeAddress, confFile)

	if errSetup != nil {
		fmt.Fprintf(os.Stderr, "Error when setting up the client library: %v\n", errSetup)
	} else {

		fmt.Println("Library set up correctly!")

	}

	rounds := 1
	roundDuration := 15.0
	executions := conf.UserCollectionMap[userId]
	for i := range rounds {
		for j, execution := range executions {
			for colName, accessType := range execution {
				funName := "readCollection"
				if accessType == "write" {
					funName = "writeCollection"
				}

				go func() {
					body, code, err := lib.ExecuteFunction(
						funName,
						"",
						map[string]string{
							"data": "write number " + strconv.Itoa(j) + "of round " + strconv.Itoa(i) + " from user " + userId,
						},
						map[string]map[string]string{
							"query": {
								"name": colName,
							},
						},
						"IT",
					)
					fmt.Println(code, string(body), err)
				}()
				time.Sleep(time.Duration((roundDuration / float64(len(executions))) * 1_000_000_000))
			}
		}
	}
}
