package functions

import (
	"fmt"
)

//ermes:export
//ermes:version 1.0.0
func authFunction(authToken string) (int, string) {
	fmt.Println("Authenticating...")
	return 200, "userId"
}
