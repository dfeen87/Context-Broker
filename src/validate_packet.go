package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/santhosh-tekuri/jsonschema/v5"
)

var ttlRe = regexp.MustCompile(`^(\d+)([smhd])$`)

func parseTTL(s string) (time.Duration, error) {
	trimmed := strings.TrimSpace(strings.ToLower(s))
	m := ttlRe.FindStringSubmatch(trimmed)
	if m == nil {
		return 0, errors.New("ttl must match <int><s|m|h|d>")
	}

	var n int
	fmt.Sscanf(m[1], "%d", &n)
	if n <= 0 {
		return 0, errors.New("ttl must be positive")
	}

	switch m[2] {
	case "s":
		return time.Second * time.Duration(n), nil
	case "m":
		return time.Minute * time.Duration(n), nil
	case "h":
		return time.Hour * time.Duration(n), nil
	case "d":
		return 24 * time.Hour * time.Duration(n), nil
	default:
		return 0, errors.New("unsupported ttl unit")
	}
}

func main() {
	packetPath := flag.String("packet", "", "Path to packet JSON")
	schemaPath := flag.String("schema", "schemas/context_packet.schema.v0.1.json", "Path to schema")
	flag.Parse()

	if *packetPath == "" {
		fmt.Fprintln(os.Stderr, "missing --packet")
		os.Exit(2)
	}

	schemaCompiler := jsonschema.NewCompiler()
	schemaFile, err := os.Open(*schemaPath)
	if err != nil {
		fail("SCHEMA_LOAD_ERROR", err)
	}
	defer schemaFile.Close()

	if err := schemaCompiler.AddResource("schema.json", schemaFile); err != nil {
		fail("SCHEMA_LOAD_ERROR", err)
	}

	schema, err := schemaCompiler.Compile("schema.json")
	if err != nil {
		fail("SCHEMA_COMPILE_ERROR", err)
	}

	packetBytes, err := os.ReadFile(*packetPath)
	if err != nil {
		fail("PACKET_READ_ERROR", err)
	}

	var packet map[string]any
	if err := json.Unmarshal(packetBytes, &packet); err != nil {
		fail("PACKET_PARSE_ERROR", err)
	}

	if err := schema.Validate(packet); err != nil {
		fail("SCHEMA_VIOLATION", err)
	}

	createdAtStr, ok := packet["created_at"].(string)
	if !ok {
		fail("TIME_INVALID_CREATED_AT", "created_at must be a string")
	}
	createdAt, err := time.Parse(time.RFC3339Nano, createdAtStr)
	if err != nil {
		fail("TIME_INVALID_CREATED_AT", err)
	}

	expiresAtStr, ok := packet["expires_at"].(string)
	if !ok {
		fail("TIME_INVALID_EXPIRES_AT", "expires_at must be a string")
	}
	expiresAt, err := time.Parse(time.RFC3339Nano, expiresAtStr)
	if err != nil {
		fail("TIME_INVALID_EXPIRES_AT", err)
	}

	ttlStr, ok := packet["ttl"].(string)
	if !ok {
		fail("TIME_INVALID_TTL", "ttl must be a string")
	}
	ttl, err := parseTTL(ttlStr)
	if err != nil {
		fail("TIME_INVALID_TTL", err)
	}

	expected := createdAt.Add(ttl)
	if !expiresAt.Equal(expected) {
		fail("TIME_MISMATCH", "expires_at != created_at + ttl")
	}

	if time.Now().UTC().After(expiresAt) {
		fail("TIME_EXPIRED", "context packet expired")
	}

	fmt.Println(`{"ok":true}`)
	os.Exit(0)
}

func fail(code string, err any) {
	out := map[string]any{
		"ok": false,
		"issues": []map[string]string{
			{"code": code, "message": fmt.Sprint(err)},
		},
	}
	b, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(b))
	os.Exit(1)
}
