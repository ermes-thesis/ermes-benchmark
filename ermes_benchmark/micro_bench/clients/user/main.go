package main

import (
	"encoding/json"
	ermes "ermes_client_library"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

type Config struct {
	CollectionPositions map[string]int                 `json:"collection_positions"`
	UserAssignments     map[string]int                 `json:"user_assignments"`
	UserCollectionMap   map[string][]map[string]string `json:"user_collection_map"`
}

func main() {

	if len(os.Args) < 2 {
		log.Fatal("Missing required arguments")
	}

	// Call the library setup
	confFile := "config.yaml"

	var conf Config
	confBytes, err := os.ReadFile(os.Args[1])
	if err != nil {
		log.Fatalf("Error reading config file: %v", err)
	}
	err = json.Unmarshal(confBytes, &conf)
	if err != nil {
		log.Fatalf("Error unmarshalling config file: %v", err)
	}

	wg := sync.WaitGroup{}

	for userId, position := range conf.UserAssignments {
		wg.Go(func() {

			nodeAddress := "10.10.101." + fmt.Sprint(position) + ":12345"

			id, err := strconv.Atoi(strings.Split(userId, "_")[1])
			if err != nil {
				log.Fatalf("Error converting user id to int")
			}
			fmt.Printf("Node address: %s", nodeAddress)

			client, errSetup := ermes.SetupClientLibrary(uint64(id), nodeAddress, confFile)
			if errSetup != nil {
				fmt.Fprintf(os.Stderr, "Error when setting up the client library: %v\n", errSetup)
			} else {
				fmt.Println("Library set up correctly!")
			}

			rounds := 10
			roundDuration := 15.0
			executions := conf.UserCollectionMap[userId]
			for i := range rounds {
				for j, execution := range executions {
					for colName, accessType := range execution {
						funName := "readCollection"
						if accessType == "write" {
							funName = "writeCollection"
						}

						wg.Go(func() {
							body, code, err := client.ExecuteFunction(
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
						})
						time.Sleep(time.Duration((roundDuration / float64(len(executions))) * 1_000_000_000))
					}
				}
			}
		})
	}

	wg.Wait()
	fmt.Println("Done")
}
