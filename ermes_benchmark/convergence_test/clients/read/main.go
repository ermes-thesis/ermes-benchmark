package main

import (
	lib "ermes_client_library"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"
)

func main() {

	clientId := 54321
	geolocation := ""
	nodeAddress := ""

	if len(os.Args) < 2 {
		log.Fatal("Missing node address argument")
	}

	nodeAddress = os.Args[1]

	if len(os.Args) > 2 {
		newId, err := strconv.Atoi(os.Args[2])
		if err != nil {
			fmt.Fprintln(os.Stderr, "Error: the client id has to be an integer. Using default value: ", clientId)
		} else {
			clientId = newId
		}
	}

	if len(os.Args) > 3 {
		geolocation = os.Args[3]
	}

	colNames := os.Args[4:]

	// Call the library setup

	confFile := "config.yaml"

	fmt.Println("Hello world !")

	errSetup := lib.SetupClientLibrary(uint64(clientId), nodeAddress, confFile)

	if errSetup != nil {
		fmt.Fprintf(os.Stderr, "Error when setting up the client library: %v\n", errSetup)
	} else {

		fmt.Println("Library set up correctly!")

	}

	rounds := 10
	functionsForRound := 50
	roundDuration := 15.0

	for i := 0; i < functionsForRound*rounds; i++ {
		go func() {
			for _, colName := range colNames {
				body, code, err := lib.ExecuteFunction(
					"functionReadSeqCollections",
					"",
					map[string]string{},
					map[string]map[string]string{
						"query": {
							"name": colName,
						},
					},
					geolocation,
				)
				fmt.Println(code, string(body), err)
			}
		}()
		time.Sleep(time.Duration((roundDuration / float64(functionsForRound)) * 1_000_000_000))
	}
}
