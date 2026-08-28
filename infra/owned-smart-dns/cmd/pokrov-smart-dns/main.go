package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/Kiwunaka/portal/infra/owned-smart-dns/internal/smartdns"
)

func main() {
	configPath := flag.String("config", "", "absolute path to the runtime configuration")
	checkOnly := flag.Bool("check", false, "validate configuration and policy, then exit")
	flag.Parse()
	if *configPath == "" {
		log.Fatal("configuration path is required")
	}

	config, policy, err := smartdns.LoadRuntime(*configPath)
	if err != nil {
		log.Fatalf("configuration rejected: %v", err)
	}
	server, err := smartdns.NewServer(config, policy)
	if err != nil {
		log.Fatalf("server initialization failed: %v", err)
	}
	if *checkOnly {
		fmt.Printf("configuration valid; policy_sha256=%s\n", policy.SHA256())
		return
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	log.Printf("POKROV Smart DNS lab listening; policy_sha256=%s", policy.SHA256())
	if err := server.Run(ctx); err != nil {
		log.Fatalf("server stopped with error: %v", err)
	}
}
