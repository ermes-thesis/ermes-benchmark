package functions

import "github.com/ermes-thesis/ermes-sdk-go"

//ermes:export
//ermes:version 1.0.0
//ermes:name readCollection
//ermes:template query
//ermes:strongCollWriteAccess false
func functionReadCollection(req map[string]string, ctx ermes.Context) (int, any) {
	coll := ctx.GetCollection("test")

	value, err := coll.Get("test_record")
	if err != nil {
		return 500, "Error getting record: " + err.Error()
	}

	return 200, value
}
