package main

import (
	lib "ermes_client_library"
	"fmt"
	"os"
	"strconv"
	"time"
)

func main() {

	// Parse the client id from the command line

	clientId := 54321

	if len(os.Args) < 2 {
		fmt.Println("No client id passed to the application. Using default value: ", clientId)
	} else {
		newId, err := strconv.Atoi(os.Args[1])
		if err != nil {
			fmt.Fprintln(os.Stderr, "Error: the client id has to be an integer. Using default value: ", clientId)
		} else {
			clientId = newId
		}
	}

	// Call the library setup

	nodeAddress := "10.10.101.54:12345"

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

	for i := 0; i < rounds; i++ {
		for i := 0; i < functionsForRound; i++ {
			go func() {
				body, code, err := lib.ExecuteFunction(
					"functionReadSeqCollections",
					"",
					map[string]string{},
					map[string]map[string]string{
						"query": {
							"name": "my_new_collection",
						},
					},
					"",
				)
				fmt.Println(code, string(body), err)
			}()
			time.Sleep(time.Duration((roundDuration / float64(functionsForRound)) * 1_000_000_000))
		}
	}
}
