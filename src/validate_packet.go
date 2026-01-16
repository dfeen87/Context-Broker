package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/santhosh-tekuri/jsonschema/v5"
)

var ttlRe = regexp.MustCompile(`^(\d+)([smhd])$`)

func parseDuration(s string, label string) (time.Duration, error) {
	trimmed := strings.TrimSpace(strings.ToLower(s))
	m := ttlRe.FindStringSubmatch(trimmed)
	if m == nil {
		return 0, fmt.Errorf("%s must match <int><s|m|h|d>", label)
	}

	n, err := strconv.Atoi(m[1])
	if err != nil {
		return 0, fmt.Errorf("%s must start with an integer", label)
	}
	if n <= 0 {
		return 0, fmt.Errorf("%s must be positive", label)
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
	schemaPath := flag.String("schema", "schemas/context_packet.schema.v1.0.0.json", "Path to schema")
	clockSkewStr := flag.String("clock-skew", "60s", "Allowed clock skew tolerance (e.g., 60s, 5m)")
	allowFutureStr := flag.String("allow-future-created-at", "5m", "Allowed future offset for created_at")
	flag.Parse()

	if *packetPath == "" {
		fmt.Fprintln(os.Stderr, "missing --packet")
		os.Exit(2)
	}

	clockSkew, err := parseDuration(*clockSkewStr, "clock-skew")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}

	allowFuture, err := parseDuration(*allowFutureStr, "allow-future-created-at")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
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
	ttl, err := parseDuration(ttlStr, "ttl")
	if err != nil {
		fail("TIME_INVALID_TTL", err)
	}

	expected := createdAt.Add(ttl)
	diff := expiresAt.Sub(expected)
	if diff < 0 {
		diff = -diff
	}
	tolerance := clockSkew
	if tolerance < time.Second {
		tolerance = time.Second
	}
	if diff > tolerance {
		fail("TIME_MISMATCH", "expires_at != created_at + ttl")
	}

	now := time.Now().UTC()
	if createdAt.Sub(now) > allowFuture {
		fail("TIME_CREATED_AT_IN_FUTURE", "created_at is too far in the future")
	}

	if now.Sub(expiresAt) > clockSkew {
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
	b, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		fmt.Printf("{\"ok\":false,\"issues\":[{\"code\":\"%s\",\"message\":\"failed to serialize error response: %s\"}]}\n", code, err)
		os.Exit(1)
	}
	fmt.Println(string(b))
	os.Exit(1)
}
