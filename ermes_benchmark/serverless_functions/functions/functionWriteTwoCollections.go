package functions

import "github.com/ermes-thesis/ermes-sdk-go"

//ermes:export
//ermes:version 1.0.0
//ermes:name writeTwoCollections
//ermes:template querySequentialAndEventual
//ermes:strongCollWriteAccess true
func functionWriteTwoCollections(req map[string]string, ctx ermes.Context) (int, any) {
	colls := ctx.GetCollections("sequentialAndEventual")

	for _, coll := range colls {
		err := coll.Put("test_record", req["data"])
		if err != nil {
			return 500, "Error getting record: " + err.Error()
		}
	}

	return 200, "ok"
}
