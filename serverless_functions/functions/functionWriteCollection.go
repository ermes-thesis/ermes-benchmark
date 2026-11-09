package functions

import (
	"strconv"

	"github.com/ermes-thesis/ermes-sdk-go"
)

//ermes:export
//ermes:version 1.0.0
//ermes:name writeCollection
//ermes:template query
//ermes:strongCollWriteAccess true
func functionWriteCollection(req map[string]string, ctx ermes.Context) (int, any) {
	coll := ctx.GetCollection("test")
	if coll == nil {
		return 500, "Collection 'test' not found"
	}

	accesses := 1
	if val, ok := req["accesses"]; ok {
		var err error
		accesses, err = strconv.Atoi(val)
		if err != nil {
			return 400, "Invalid accesses parameter: " + err.Error()
		}
	}

	for i := 0; i < accesses; i++ {
		err := coll.Put("test_record_"+strconv.Itoa(i), req["data"])
		if err != nil {
			return 500, "Error writing record: " + err.Error()
		}
	}

	return 200, "ok"
}
