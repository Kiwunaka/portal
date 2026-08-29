package smartdns

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"sync"
	"time"
)

type Server struct {
	config     Config
	policy     *Policy
	resolver   originResolver
	limiter    *sourceLimiter
	doh        *channelListener
	httpServer *http.Server
	global     chan struct{}
}

func NewServer(config Config, policy *Policy) (*Server, error) {
	certificate, err := loadServerCertificate(config)
	if err != nil {
		return nil, err
	}
	limiter := newSourceLimiter(
		config.Limits.MaxTrackedSourceIPs,
		config.Limits.MaxDoHRequestsPerMinute,
		time.Minute,
	)
	dohListener := newChannelListener(config.Listen)
	tlsConfig := &tls.Config{
		MinVersion:   tls.VersionTLS12,
		Certificates: []tls.Certificate{certificate},
		NextProtos:   []string{"h2", "http/1.1"},
	}
	return &Server{
		config:   config,
		policy:   policy,
		resolver: newDoTResolver(config),
		limiter:  limiter,
		doh:      dohListener,
		global:   make(chan struct{}, config.Limits.MaxConcurrentConnections),
		httpServer: &http.Server{
			Handler:           newDoHHandler(config, policy, limiter),
			TLSConfig:         tlsConfig,
			ReadHeaderTimeout: config.Limits.handshakeTimeout(),
			ReadTimeout:       config.Limits.idleTimeout(),
			WriteTimeout:      config.Limits.idleTimeout(),
			IdleTimeout:       config.Limits.idleTimeout(),
			MaxHeaderBytes:    8 << 10,
			ErrorLog:          log.New(io.Discard, "", 0),
		},
	}, nil
}

func loadServerCertificate(config Config) (tls.Certificate, error) {
	if runtime.GOOS != "windows" {
		info, err := os.Stat(config.TLSPrivateKeyPath)
		if err != nil {
			return tls.Certificate{}, err
		}
		if !info.Mode().IsRegular() || info.Mode().Perm()&0o027 != 0 {
			return tls.Certificate{}, errors.New("TLS private key permissions are too broad")
		}
	}
	certificate, err := tls.LoadX509KeyPair(config.TLSCertificatePath, config.TLSPrivateKeyPath)
	if err != nil {
		return tls.Certificate{}, err
	}
	if len(certificate.Certificate) == 0 {
		return tls.Certificate{}, errors.New("TLS certificate chain is empty")
	}
	leaf, err := x509.ParseCertificate(certificate.Certificate[0])
	if err != nil {
		return tls.Certificate{}, err
	}
	if err := leaf.VerifyHostname(config.DoHHostname); err != nil {
		return tls.Certificate{}, errors.New("TLS certificate does not cover the DoH hostname")
	}
	now := time.Now()
	if now.Before(leaf.NotBefore) || !now.Before(leaf.NotAfter) {
		return tls.Certificate{}, errors.New("TLS certificate is not currently valid")
	}
	certificate.Leaf = leaf
	return certificate, nil
}

func (s *Server) Run(ctx context.Context) error {
	listener, err := net.Listen("tcp", s.config.Listen)
	if err != nil {
		return err
	}
	defer listener.Close()
	defer s.doh.Close()
	defer s.httpServer.Close()
	serveErrors := make(chan error, 1)
	go func() {
		serveErr := s.httpServer.ServeTLS(s.doh, "", "")
		serveErrors <- serveErr
		if serveErr != nil && !errors.Is(serveErr, http.ErrServerClosed) && !errors.Is(serveErr, net.ErrClosed) {
			_ = listener.Close()
		}
	}()
	go func() {
		<-ctx.Done()
		_ = listener.Close()
		_ = s.doh.Close()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		_ = s.httpServer.Shutdown(shutdownCtx)
	}()

	for {
		connection, err := listener.Accept()
		if err != nil {
			if ctx.Err() != nil || errors.Is(err, net.ErrClosed) {
				select {
				case serveErr := <-serveErrors:
					if serveErr != nil && !errors.Is(serveErr, http.ErrServerClosed) && !errors.Is(serveErr, net.ErrClosed) {
						return serveErr
					}
				default:
				}
				return nil
			}
			return err
		}
		select {
		case s.global <- struct{}{}:
			go s.handle(connection)
		default:
			_ = connection.Close()
		}
		select {
		case serveErr := <-serveErrors:
			if serveErr != nil && !errors.Is(serveErr, http.ErrServerClosed) && !errors.Is(serveErr, net.ErrClosed) {
				return serveErr
			}
		default:
		}
	}
}

func (s *Server) handle(connection net.Conn) {
	if s.config.AcceptProxyProtocolV2 {
		proxied, err := acceptProxyProtocolV2(connection, s.config.Limits.handshakeTimeout())
		if err != nil {
			<-s.global
			_ = connection.Close()
			return
		}
		connection = proxied
	}
	source := remoteHost(connection.RemoteAddr().String())
	if source == "" || !s.limiter.acquireConnection(source, s.config.Limits.MaxConnectionsPerIP) {
		<-s.global
		_ = connection.Close()
		return
	}
	owned := &releaseConn{
		Conn: connection,
		release: func() {
			s.limiter.releaseConnection(source)
			<-s.global
		},
	}
	prefix, serverName, err := sniffClientHello(
		owned,
		s.config.Limits.MaxClientHelloBytes,
		s.config.Limits.handshakeTimeout(),
	)
	if err != nil {
		_ = owned.Close()
		return
	}
	replayed := &prefixConn{Conn: owned, prefix: bytes.NewReader(prefix)}
	if serverName == s.config.DoHHostname {
		if !s.doh.offer(replayed) {
			_ = replayed.Close()
		}
		return
	}
	if !s.policy.Allows(serverName) {
		_ = replayed.Close()
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), s.config.Limits.connectTimeout())
	origin, err := dialOrigin(ctx, s.resolver, serverName, s.config.Limits.connectTimeout())
	cancel()
	if err != nil {
		_ = replayed.Close()
		return
	}
	proxyBidirectional(
		replayed,
		origin,
		s.config.Limits.idleTimeout(),
		s.config.Limits.maxConnectionLifetime(),
		s.config.Limits.MaxBytesPerDirection,
	)
}

func proxyBidirectional(client, origin net.Conn, idleTimeout, maximumLifetime time.Duration, maximumBytes int64) {
	defer client.Close()
	defer origin.Close()
	client = &deadlineConn{Conn: client, idle: idleTimeout, absolute: time.Now().Add(maximumLifetime)}
	origin = &deadlineConn{Conn: origin, idle: idleTimeout, absolute: time.Now().Add(maximumLifetime)}
	done := make(chan struct{}, 2)
	copyOne := func(destination, source net.Conn) {
		_, _ = io.CopyN(destination, source, maximumBytes)
		if closer, ok := destination.(interface{ CloseWrite() error }); ok {
			_ = closer.CloseWrite()
		}
		done <- struct{}{}
	}
	go copyOne(origin, client)
	go copyOne(client, origin)
	<-done
	_ = client.SetDeadline(time.Now())
	_ = origin.SetDeadline(time.Now())
	<-done
}

type prefixConn struct {
	net.Conn
	prefix *bytes.Reader
}

func (c *prefixConn) Read(buffer []byte) (int, error) {
	if c.prefix.Len() > 0 {
		return c.prefix.Read(buffer)
	}
	return c.Conn.Read(buffer)
}

type releaseConn struct {
	net.Conn
	once    sync.Once
	release func()
}

func (c *releaseConn) Close() error {
	err := c.Conn.Close()
	c.once.Do(c.release)
	return err
}

type deadlineConn struct {
	net.Conn
	idle     time.Duration
	absolute time.Time
}

func (c *deadlineConn) nextDeadline() time.Time {
	idle := time.Now().Add(c.idle)
	if idle.After(c.absolute) {
		return c.absolute
	}
	return idle
}

func (c *deadlineConn) Read(buffer []byte) (int, error) {
	_ = c.Conn.SetReadDeadline(c.nextDeadline())
	return c.Conn.Read(buffer)
}

func (c *deadlineConn) Write(buffer []byte) (int, error) {
	_ = c.Conn.SetWriteDeadline(c.nextDeadline())
	return c.Conn.Write(buffer)
}

type channelListener struct {
	connections chan net.Conn
	closed      chan struct{}
	once        sync.Once
	address     net.Addr
}

func newChannelListener(address string) *channelListener {
	return &channelListener{
		connections: make(chan net.Conn, 64),
		closed:      make(chan struct{}),
		address:     staticAddr(address),
	}
}

func (l *channelListener) offer(connection net.Conn) bool {
	select {
	case l.connections <- connection:
		return true
	case <-l.closed:
		return false
	default:
		return false
	}
}

func (l *channelListener) Accept() (net.Conn, error) {
	select {
	case connection := <-l.connections:
		return connection, nil
	case <-l.closed:
		return nil, net.ErrClosed
	}
}

func (l *channelListener) Close() error {
	l.once.Do(func() { close(l.closed) })
	return nil
}

func (l *channelListener) Addr() net.Addr { return l.address }

type staticAddr string

func (a staticAddr) Network() string { return "tcp" }
func (a staticAddr) String() string  { return string(a) }
