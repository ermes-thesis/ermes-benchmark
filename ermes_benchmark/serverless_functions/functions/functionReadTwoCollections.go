package functions

import "github.com/ermes-thesis/ermes-sdk-go"

//ermes:export
//ermes:version 1.0.0
//ermes:name readTwoCollections
//ermes:template querySequentialAndEventual
//ermes:strongCollWriteAccess false
func functionReadTwoCollections(req map[string]string, ctx ermes.Context) (int, any) {
	colls := ctx.GetCollections("sequentialAndEventual")

	var values []string
	for _, coll := range colls {
		metadata, _ := coll.GetMetadata()
		if metadata.Consistency == ermes.EventualConsistent {
			err := coll.Put("test_record", req["data"])
			if err != nil {
				return 500, "Error getting record: " + err.Error()
			}
		} else {
			value, err := coll.Get("test_record")
			if err != nil {
				return 500, "Error getting record: " + err.Error()
			}
			values = append(values, value)
		}
	}

	return 200, values
}
