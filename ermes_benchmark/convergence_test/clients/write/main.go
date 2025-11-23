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

	clientId := 12345
	geolocation := ""

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

	if len(os.Args) >= 2 {
		geolocation = os.Args[2]
	}

	// Call the library setup

	nodeAddress := "10.10.101.51:12345"

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
			body, code, err := lib.ExecuteFunction(
				"functionUseSeqCollections",
				"",
				map[string]string{"data": "write number " + strconv.Itoa(i)},
				map[string]map[string]string{
					"query": {
						"name": "my_new_collection",
					},
				},
				geolocation,
			)
			fmt.Println(code, string(body), err)
		}()
		time.Sleep(time.Duration((roundDuration / float64(functionsForRound)) * 1_000_000_000))
	}
}
