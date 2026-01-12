package functions

import "github.com/ermes-thesis/ermes-sdk-go"

//ermes:export
//ermes:version 1.0.0
//ermes:name createCollection
func functionCreateCollection(req map[string]string, ctx ermes.Context) (int, any) {
	consistency := ermes.EventualConsistent
	if req["consistency"] == "sequential" {
		consistency = ermes.SequentialConsistent
	}
	_, err := ctx.CreateCollection(req["name"], consistency, req["geolocation"], []string{"groupA"}, nil, false)
	if err != nil {
		return 500, "Error creating collection: " + err.Error()
	}

	return 200, "Collection created successfully"
}
