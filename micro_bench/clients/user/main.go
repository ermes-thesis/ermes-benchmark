package main

import (
	"encoding/json"
	ermes "ermes_client_library"
	"fmt"
	"log"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
)

type Config struct {
	CollectionPositions map[string]int                 `json:"collection_positions"`
	UserAssignments     map[string]int                 `json:"user_assignments"`
	UserCollectionMap   map[string][]map[string]string `json:"user_collection_map"`
}

// subnetPrefix builds node addresses as "<subnet>.<tree-node-id>"; the subnet
// is taken from the ERMES_SUBNET environment variable (default 10.10.101).
var subnetPrefix = func() string {
	if s := os.Getenv("ERMES_SUBNET"); s != "" {
		return s + "."
	}
	return "10.10.101."
}()

func main() {
	logger, err := logger.NewLogger(logger.Config{
		Level:  logger.InfoLevel,
		Format: "text",
		Output: &logger.LogFile{
			LogDir:      "results",
			LogFileName: "user.log",
		},
	})
	if err != nil {
		log.Fatalf("Error creating logger: %v", err)
	}
	defer logger.Close()

	if len(os.Args) < 2 {
		logger.Error("Missing required arguments: ./user <config_file> [accesses_param]")
		return
	}

	// Call the library setup
	confFile := "config.yaml"
	random := rand.New(rand.NewSource(0))

	numAccesses := "1"
	if len(os.Args) > 2 {
		numAccesses = os.Args[2]
	}
	logger.Infof("Passing 'accesses' parameter to function: %s\n", numAccesses)

	numRounds := 10
	if len(os.Args) > 3 {
		r, err := strconv.Atoi(os.Args[3])
		if err != nil {
			logger.Errorf("Error converting rounds argument to int: %v", err)
			return
		}
		numRounds = r
	}
	logger.Infof("numRounds: %d\n", numRounds)

	var conf Config
	confBytes, err := os.ReadFile(os.Args[1])
	if err != nil {
		logger.Errorf("Error reading config file: %v", err)
		return
	}
	err = json.Unmarshal(confBytes, &conf)
	if err != nil {
		logger.Errorf("Error unmarshalling config file: %v", err)
		return
	}

	wg := sync.WaitGroup{}

	for userId, position := range conf.UserAssignments {
		wg.Go(func() {

			nodeAddress := subnetPrefix + fmt.Sprint(position) + ":12345"

			id, err := strconv.Atoi(strings.Split(userId, "_")[1])
			if err != nil {
				logger.Errorf("Error converting user id to int")
				return
			}
			logger.Infof("Node address: %s", nodeAddress)

			client, errSetup := ermes.SetupClientLibrary(uint64(id), nodeAddress, confFile)
			if errSetup != nil {
				logger.Errorf("Error when setting up the client library: %v\n", errSetup)
				return
			}
			logger.Info("Library set up correctly!")

			sleep := random.Intn(600)
			time.Sleep(time.Duration(sleep) * time.Millisecond)

			roundDuration := 15.0
			executions := conf.UserCollectionMap[userId]
			for i := range numRounds {
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
									"data":     "write number " + strconv.Itoa(j) + " of round " + strconv.Itoa(i) + " from user " + userId,
									"accesses": numAccesses,
								},
								map[string]map[string]string{
									"query": {
										"name": colName,
									},
								},
								"IT",
							)
							logger.Infof("Status %d, %s, error: %v", code, string(body), err)
						})
						time.Sleep(time.Duration((roundDuration / float64(len(executions))) * 1_000_000_000))
					}
				}
			}
		})
	}

	wg.Wait()
	logger.Info("Done")
}
