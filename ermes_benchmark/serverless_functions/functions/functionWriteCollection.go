package functions

import "github.com/ermes-thesis/ermes-sdk-go"

//ermes:export
//ermes:version 1.0.0
//ermes:name writeCollection
//ermes:template query
//ermes:strongCollWriteAccess true
func functionWriteCollection(req map[string]string, ctx ermes.Context) (int, any) {
	coll := ctx.GetCollection("test")

	err := coll.Put("test_record", req["data"])
	if err != nil {
		return 500, "Error getting record: " + err.Error()
	}

	return 200, "ok"
}
