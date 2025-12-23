package wasm_bench

import (
	"github.com/ermes-thesis/ermes-sdk-go"
)

//ermes:export
//ermes:name statefulFunction
func statefulFunction(req map[string]string, ctx ermes.Context) (int, any) {
	coll := ctx.GetCollection("test_collection")

	coll.Get("battiti")

	coll.Put("prova", "Hello world")
	coll.Get("prova")

	newColl, _ := ctx.CreateCollection("nuova_collection", ermes.EventualConsistent, "IT", []string{"test", "pippo"}, make(map[string]string), false)
	newColl.Put("nuovo_record", "CIAOOOOOO")
	newColl.Get("nuovo_record")

	newColl.Put("test", "pippo")
	newColl.Get("test")
	newColl.Delete("test")
	newColl.Get("test")

	coll.MultipleGet("testMGET", "testMGET2")

	ctx.DeleteCollection(coll)

	collMGET, _ := ctx.CreateCollection("multiple_get_coll", ermes.EventualConsistent, "IT/Milan", []string{"test", "fake"}, make(map[string]string), false)
	collMGET.Put("new_record", "something")
	collMGET.Put("another_record", "something else")
	collMGET.Put("third_record", "test")

	collMGET.MultipleGet("new_record", "another_record", "third_record", "cicico")

	return 200, "ok"
}
