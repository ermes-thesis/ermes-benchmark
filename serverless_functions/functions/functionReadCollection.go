package functions

import (
	"strconv"

	"github.com/ermes-thesis/ermes-sdk-go"
)

//ermes:export
//ermes:version 1.0.0
//ermes:name readCollection
//ermes:template query
//ermes:strongCollWriteAccess false
func functionReadCollection(req map[string]string, ctx ermes.Context) (int, any) {
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

	values := make([]string, 0, accesses)
	for i := 0; i < accesses; i++ {
		v, err := coll.Get("test_record_" + strconv.Itoa(i))
		if err != nil {
			return 500, "Error getting record: " + err.Error()
		}
		values = append(values, v)
	}

	return 200, values
}
