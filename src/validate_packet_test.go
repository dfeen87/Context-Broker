package main

import (
	"strings"
	"testing"
)

func TestDecodePacketRejectsDuplicateKeys(t *testing.T) {
	_, err := decodePacket([]byte(`{"context_id":"first","context_id":"second"}`))
	if err == nil || !strings.Contains(err.Error(), "duplicate object key") {
		t.Fatalf("expected duplicate-key error, got %v", err)
	}
}

func TestDecodePacketRejectsNestedDuplicateKeys(t *testing.T) {
	_, err := decodePacket([]byte(`{"payload":{"value":1,"value":2}}`))
	if err == nil || !strings.Contains(err.Error(), "duplicate object key") {
		t.Fatalf("expected nested duplicate-key error, got %v", err)
	}
}

func TestDecodePacketRejectsOversizeInput(t *testing.T) {
	_, err := decodePacket([]byte(strings.Repeat("x", maxPacketBytes+1)))
	if err == nil || !strings.Contains(err.Error(), "maximum size") {
		t.Fatalf("expected size error, got %v", err)
	}
}

func TestDecodePacketRejectsTrailingJSON(t *testing.T) {
	_, err := decodePacket([]byte(`{} {}`))
	if err == nil {
		t.Fatal("expected trailing JSON to be rejected")
	}
}
