package main

import (
	lib "ermes_client_library"
	"fmt"
	"log"
	"os"
	"strconv"
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

	consistency := "sequential"
	if len(os.Args) > 5 {
		consistency = os.Args[5]
	}

	// Call the library setup

	confFile := "config.yaml"

	fmt.Println("Hello world !")

	errSetup := lib.SetupClientLibrary(uint64(clientId), nodeAddress, confFile)

	if errSetup != nil {
		fmt.Fprintf(os.Stderr, "Error when setting up the client library: %v\n", errSetup)
	} else {

		fmt.Println("Library set up correctly!")

	}

	body, code, err := lib.ExecuteFunction(
		"createCollection",
		"",
		map[string]string{
			"name":        collectionName,
			"consistency": consistency,
			"geolocation": geolocation,
		},
		map[string]map[string]string{},
		"",
	)
	fmt.Println(code, string(body), err)

}
