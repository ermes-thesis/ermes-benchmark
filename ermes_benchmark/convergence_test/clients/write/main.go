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

	clientId := 12345
	collectionName := ""
	geolocation := ""
	nodeAddress := ""

	if len(os.Args) < 3 {
		log.Fatal("Missing node address argument")
	}

	nodeAddress = os.Args[1]
	collectionName = os.Args[2]

	if len(os.Args) > 3 {
		newId, err := strconv.Atoi(os.Args[3])
		if err != nil {
			fmt.Fprintln(os.Stderr, "Error: the client id has to be an integer. Using default value: ", clientId)
		} else {
			clientId = newId
		}
	}

	if len(os.Args) > 4 {
		geolocation = os.Args[4]
	}

	// Call the library setup

	confFile := "config.yaml"

	fmt.Println("Hello world !")

	client, errSetup := lib.SetupClientLibrary(uint64(clientId), nodeAddress, confFile)

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
			body, code, err := client.ExecuteFunction(
				"writeCollection",
				"",
				map[string]string{
					"data": "write number " + strconv.Itoa(i),
				},
				map[string]map[string]string{
					"query": {
						"name": collectionName,
					},
				},
				geolocation,
			)
			fmt.Println(code, string(body), err)
		}()
		time.Sleep(time.Duration((roundDuration / float64(functionsForRound)) * 1_000_000_000))
	}
}
